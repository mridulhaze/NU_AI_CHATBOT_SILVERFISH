"""
FAQ Service for National University AI Assistant
Manages parsing, indexing, searching, liking, and top-ranking FAQs from FAQ/faq.txt.
"""

import os
import re
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from db.sql_store import get_sql_store, SQLStore

logger = logging.getLogger("NU_FAQ_SERVICE")


def clean_category_name(raw: str) -> str:
    """Cleans raw category line into a clean, human-readable category name."""
    s = re.sub(r"\(.*?\)", "", raw).strip()
    s = re.sub(r"^(ক্যাটাগরি|বিষয়|বিভাগ|অধ্যায়)\s*[\d০-৯]+[:\s\-]*", "", s).strip()
    if s.startswith(":"):
        s = s[1:].strip()
    return s.strip() or "সাধারণ তথ্য"


class FAQService:
    def __init__(self, sql_store: Optional[SQLStore] = None):
        self.sql_store = sql_store or get_sql_store()
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.faq_file_path = self.base_dir / "FAQ" / "faq.txt"

    def parse_faq_file(self, file_path: Optional[Path] = None) -> List[Dict[str, Any]]:
        target_path = file_path or self.faq_file_path
        if not target_path.exists():
            logger.warning(f"FAQ file not found at: {target_path}")
            return []

        content = target_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        entries: List[Dict[str, Any]] = []
        current_cat = "সাধারণ তথ্য"
        current_q = None
        current_a_lines = []

        q_re = re.compile(r"^\s*(\d+|[০-৯]+)\.\s*প্রশ্ন\s*:\s*(.*)", re.IGNORECASE)
        a_re = re.compile(r"^\s*উত্তর\s*:\s*(.*)", re.IGNORECASE)

        for line in lines:
            line_s = line.strip()
            if line_s.startswith(("ক্যাটাগরি", "বিষয়:", "বিভাগ:")):
                if current_q and current_a_lines:
                    ans = "\n".join(current_a_lines).strip()
                    if ans:
                        entries.append({
                            "category": current_cat,
                            "question": current_q,
                            "answer": ans
                        })
                    current_q = None
                    current_a_lines = []
                current_cat = clean_category_name(line_s)
                continue

            m_q = q_re.match(line)
            if m_q:
                if current_q and current_a_lines:
                    ans = "\n".join(current_a_lines).strip()
                    if ans:
                        entries.append({
                            "category": current_cat,
                            "question": current_q,
                            "answer": ans
                        })
                current_q = m_q.group(2).strip()
                current_a_lines = []
                continue

            m_a = a_re.match(line)
            if m_a:
                current_a_lines.append(m_a.group(1).strip())
                continue

            if current_q and current_a_lines:
                current_a_lines.append(line)

        if current_q and current_a_lines:
            ans = "\n".join(current_a_lines).strip()
            if ans:
                entries.append({
                    "category": current_cat,
                    "question": current_q,
                    "answer": ans
                })

        logger.info(f"Parsed {len(entries)} valid FAQs from {target_path.name}")
        return entries

    def sync_from_file(self, file_path: Optional[Path] = None, force: bool = False) -> Dict[str, Any]:
        """
        Synchronizes all FAQs into SQLite faq_entries idempotently.
        Preserves existing user like counts.
        """
        target_path = file_path or self.faq_file_path
        parsed_entries = self.parse_faq_file(target_path)
        if not parsed_entries:
            return {"status": "error", "message": "No FAQ entries found to sync.", "synced": 0}

        synced_count = 0
        categories_seen = set()

        for idx, entry in enumerate(parsed_entries, 1):
            cat = entry["category"]
            q = entry["question"]
            a = entry["answer"]
            categories_seen.add(cat)

            source_key = f"faq_{idx:04d}"
            # Extract keywords from question & category
            tokens = [t for t in re.split(r"[\s,;()\"'.-]+", f"{q} {cat}") if len(t) > 2]
            keywords = " ".join(dict.fromkeys(tokens))

            self.sql_store.upsert_faq_record(
                question=q,
                answer=a,
                category=cat,
                source_key=source_key,
                keywords=keywords,
                source_file="FAQ/faq.txt",
                is_active=1
            )
            synced_count += 1

        logger.info(f"Successfully synced {synced_count} FAQs across {len(categories_seen)} categories.")
        return {
            "status": "success",
            "synced": synced_count,
            "categories_count": len(categories_seen),
            "source_file": str(target_path)
        }

    def ensure_seeded(self) -> None:
        """Seeds the database with FAQs on startup if empty or below threshold."""
        try:
            with self.sql_store._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as cnt FROM faq_entries WHERE is_active = 1")
                row = cursor.fetchone()
                cnt = row["cnt"] if row else 0

            if cnt < 500:
                logger.info(f"FAQ store has {cnt} entries (< 500 threshold). Running seed import...")
                self.sync_from_file()
            else:
                logger.info(f"FAQ store already populated with {cnt} active entries.")
        except Exception as e:
            logger.error(f"Error ensuring FAQ seeding: {e}", exc_info=True)

    def list_faqs(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        sort: str = "most_liked",
        limit: int = 30,
        offset: int = 0,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        return self.sql_store.list_faqs(
            category=category,
            search=search,
            sort=sort,
            limit=limit,
            offset=offset,
            session_id=session_id
        )

    def get_top_liked(self, limit: int = 10, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.sql_store.get_top_liked_faqs(limit=limit, session_id=session_id)

    def get_by_id(self, faq_id: int, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        return self.sql_store.get_faq_by_id(faq_id=faq_id, session_id=session_id)

    def toggle_like(self, faq_id: int, session_id: str) -> Dict[str, Any]:
        if not session_id or not session_id.strip():
            session_id = "anonymous_session"
        return self.sql_store.toggle_faq_like(faq_id=faq_id, session_id=session_id.strip())

    def get_categories(self) -> List[Dict[str, Any]]:
        return self.sql_store.get_faq_categories()


# Singleton factory
_faq_service_instance: Optional[FAQService] = None

def get_faq_service() -> FAQService:
    global _faq_service_instance
    if _faq_service_instance is None:
        _faq_service_instance = FAQService()
    return _faq_service_instance
