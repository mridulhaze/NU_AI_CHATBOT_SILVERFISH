import os
import sqlite3
import hashlib
from pathlib import Path
from typing import Optional, Any
from datetime import datetime

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nu_assistant.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

class SQLStore:
    def __init__(self, db_path: Optional[str | Path] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self):
        """Run schema migrations."""
        if SCHEMA_PATH.exists():
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            with self._get_connection() as conn:
                conn.executescript(schema_sql)
                try:
                    conn.execute("ALTER TABLE academic_exam_information ADD COLUMN course_name TEXT DEFAULT '';")
                    conn.commit()
                except Exception:
                    pass

    @staticmethod
    def compute_hash(text: str) -> str:
        return hashlib.md5(text.strip().encode("utf-8")).hexdigest()

    # --- Notices CRUD ---
    def upsert_notice(self, title: str, url: str, pdf_url: Optional[str], category: str, published_date: str, raw_text: str) -> bool:
        """
        Inserts or updates a notice if content has changed.
        Returns True if new/updated, False if unchanged.
        """
        content_hash = self.compute_hash(f"{title}|{published_date}|{raw_text}")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT content_hash FROM notices WHERE url = ?", (url,))
            row = cursor.fetchone()
            if row:
                if row["content_hash"] == content_hash:
                    return False  # No change
                cursor.execute("""
                    UPDATE notices
                    SET title = ?, pdf_url = ?, category = ?, published_date = ?, content_hash = ?, raw_text = ?, scraped_at = CURRENT_TIMESTAMP
                    WHERE url = ?
                """, (title, pdf_url, category, published_date, content_hash, raw_text, url))
            else:
                cursor.execute("""
                    INSERT INTO notices (title, url, pdf_url, category, published_date, content_hash, raw_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (title, url, pdf_url, category, published_date, content_hash, raw_text))
            return True

    def get_recent_notices(self, limit: int = 15, category: Optional[str] = None) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute("""
                    SELECT * FROM notices WHERE category LIKE ? ORDER BY date_iso DESC, id DESC LIMIT ?
                """, (f"%{category}%", limit))
            else:
                cursor.execute("SELECT * FROM notices ORDER BY date_iso DESC, id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def search_notices(self, query_terms: list[str], limit: int = 10) -> list[dict[str, Any]]:
        if not query_terms:
            return self.get_recent_notices(limit=limit)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            conditions = " OR ".join(["title LIKE ? OR raw_text LIKE ?" for _ in query_terms])
            params = []
            for term in query_terms:
                params.extend([f"%{term}%", f"%{term}%"])
            params.append(limit)
            cursor.execute(f"SELECT * FROM notices WHERE {conditions} ORDER BY date_iso DESC, id DESC LIMIT ?", params)
            return [dict(row) for row in cursor.fetchall()]

    # --- Admission Info CRUD ---
    def upsert_admission_info(self, program: str, level: str, eligibility: str, deadline: str, notes: str, source_url: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM admission_info WHERE program = ? AND level = ?", (program, level))
            row = cursor.fetchone()
            if row:
                cursor.execute("""
                    UPDATE admission_info
                    SET eligibility = ?, deadline = ?, notes = ?, source_url = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (eligibility, deadline, notes, source_url, row["id"]))
            else:
                cursor.execute("""
                    INSERT INTO admission_info (program, level, eligibility, deadline, notes, source_url)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (program, level, eligibility, deadline, notes, source_url))

    def get_admission_info(self, query: Optional[str] = None) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if query:
                cursor.execute("""
                    SELECT * FROM admission_info 
                    WHERE program LIKE ? OR level LIKE ? OR notes LIKE ?
                    ORDER BY id DESC LIMIT 10
                """, (f"%{query}%", f"%{query}%", f"%{query}%"))
            else:
                cursor.execute("SELECT * FROM admission_info ORDER BY id DESC LIMIT 20")
            return [dict(row) for row in cursor.fetchall()]

    # --- FAQ & Self-Learned Entries ---
    def insert_faq_entry(self, question: str, answer: str, source_url: str = "", language: str = "bn", 
                         category: str = "General", confidence: float = 1.0, verified_by_admin: int = 0) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO faq_entries (question, answer, source_url, language, category, confidence, verified_by_admin)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (question, answer, source_url, language, category, confidence, verified_by_admin))
            return cursor.lastrowid

    def get_faqs(self, verified_only: bool = False, limit: int = 50) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if verified_only:
                cursor.execute("SELECT * FROM faq_entries WHERE verified_by_admin = 1 ORDER BY id DESC LIMIT ?", (limit,))
            else:
                cursor.execute("SELECT * FROM faq_entries ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def search_faqs(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM faq_entries 
                WHERE question LIKE ? OR answer LIKE ? 
                ORDER BY verified_by_admin DESC, confidence DESC LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
            return [dict(row) for row in cursor.fetchall()]

    # --- Gap Queue (Self-Enrichment) ---
    def log_gap(self, user_query: str, language: str = "bn", session_id: str = "", reason: str = "") -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Check if recent identical query exists in pending/researching
            cursor.execute("""
                SELECT id FROM gap_queue 
                WHERE user_query = ? AND status IN ('pending', 'candidate_ready')
            """, (user_query,))
            existing = cursor.fetchone()
            if existing:
                return existing["id"]
            cursor.execute("""
                INSERT INTO gap_queue (user_query, language, session_id, reason, status)
                VALUES (?, ?, ?, ?, 'pending')
            """, (user_query, language, session_id, reason))
            return cursor.lastrowid

    def get_gap_queue(self, status: Optional[str] = None, limit: int = 50) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT * FROM gap_queue WHERE status = ? ORDER BY id DESC LIMIT ?", (status, limit))
            else:
                cursor.execute("SELECT * FROM gap_queue ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def update_gap_status(self, gap_id: int, status: str, candidate_answer: Optional[str] = None, confidence: Optional[float] = None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            resolved_at = datetime.now().isoformat() if status in ("resolved", "rejected") else None
            cursor.execute("""
                UPDATE gap_queue
                SET status = ?, candidate_answer = COALESCE(?, candidate_answer),
                    confidence = COALESCE(?, confidence), resolved_at = ?
                WHERE id = ?
            """, (status, candidate_answer, confidence, resolved_at, gap_id))

    def approve_gap_entry(self, gap_id: int, custom_answer: Optional[str] = None) -> Optional[int]:
        """Approves a candidate gap entry and inserts it into faq_entries as verified."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM gap_queue WHERE id = ?", (gap_id,))
            gap = cursor.fetchone()
            if not gap:
                return None
            
            final_answer = custom_answer or gap["candidate_answer"] or ""
            faq_id = self.insert_faq_entry(
                question=gap["user_query"],
                answer=final_answer,
                source_url="https://www.nu.ac.bd",
                language=gap["language"] or "bn",
                category="Self-Enriched FAQ",
                confidence=1.0,
                verified_by_admin=1
            )
            self.update_gap_status(gap_id, status="resolved", candidate_answer=final_answer, confidence=1.0)
            return faq_id

    # --- Crawl Logs ---
    def start_crawl_log(self, source: str) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO crawl_log (source, status, started_at)
                VALUES (?, 'running', CURRENT_TIMESTAMP)
            """, (source,))
            return cursor.lastrowid

    def finish_crawl_log(self, log_id: int, status: str, pages_scraped: int, new_items: int, errors: str = ""):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE crawl_log
                SET status = ?, finished_at = CURRENT_TIMESTAMP, pages_scraped = ?, new_items = ?, errors = ?
                WHERE id = ?
            """, (status, pages_scraped, new_items, errors, log_id))

    # --- Officers & Employee Directory CRUD ---
    def upsert_officer(self, department_slug: str, department_name: str, department_url: str,
                       name: str, designation_bn: str, designation_en: str,
                       phone: str = "", email: str = "", raw_details: str = "") -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM officers_directory 
                WHERE department_slug = ? AND name = ?
            """, (department_slug, name))
            row = cursor.fetchone()
            if row:
                cursor.execute("""
                    UPDATE officers_directory
                    SET department_name = ?, department_url = ?, designation_bn = ?,
                        designation_en = ?, phone = ?, email = ?, raw_details = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (department_name, department_url, designation_bn, designation_en, phone, email, raw_details, row["id"]))
                return row["id"]
            else:
                cursor.execute("""
                    INSERT INTO officers_directory (department_slug, department_name, department_url, name, designation_bn, designation_en, phone, email, raw_details)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (department_slug, department_name, department_url, name, designation_bn, designation_en, phone, email, raw_details))
                return cursor.lastrowid

    def search_officers(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            pattern = f"%{query.strip()}%"
            cursor.execute("""
                SELECT * FROM officers_directory
                WHERE name LIKE ? 
                   OR designation_bn LIKE ? 
                   OR designation_en LIKE ? 
                   OR email LIKE ?
                   OR phone LIKE ?
                   OR department_name LIKE ?
                   OR department_slug LIKE ?
                ORDER BY id ASC LIMIT ?
            """, (pattern, pattern, pattern, pattern, pattern, pattern, pattern, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_officers_by_department(self, department_slug: str) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM officers_directory
                WHERE department_slug = ? OR department_name LIKE ?
                ORDER BY id ASC
            """, (department_slug, f"%{department_slug}%"))
            return [dict(row) for row in cursor.fetchall()]

    def get_all_departments_summary(self) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT department_slug, department_name, department_url, COUNT(*) as officer_count, MAX(updated_at) as last_updated
                FROM officers_directory
                GROUP BY department_slug
                ORDER BY department_name ASC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_crawl_logs(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM crawl_log ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # --- Many-to-Many Q&A Knowledge Base CRUD ---
    def insert_qa_knowledge(
        self, 
        primary_question: str, 
        category: str = "General", 
        tags: str = "",
        question_variants: Optional[list[str]] = None,
        answer_variants: Optional[list[dict[str, Any]]] = None
    ) -> int:
        """
        Inserts a primary Q&A with multiple related question variants and multiple answer variants.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO qa_knowledge_base (primary_question, category, tags)
                VALUES (?, ?, ?)
            """, (primary_question.strip(), category.strip(), tags.strip()))
            qa_id = cursor.lastrowid

            # Insert question variants
            variants = question_variants or []
            if primary_question.strip() not in variants:
                variants.append(primary_question.strip())
            for q_var in variants:
                if q_var and q_var.strip():
                    cursor.execute("""
                        INSERT INTO qa_question_variants (qa_id, question_text)
                        VALUES (?, ?)
                    """, (qa_id, q_var.strip()))

            # Insert answer variants
            answers = answer_variants or []
            for ans in answers:
                if isinstance(ans, str) and ans.strip():
                    cursor.execute("""
                        INSERT INTO qa_answer_variants (qa_id, answer_text, is_primary, language)
                        VALUES (?, ?, 1, 'bn')
                    """, (qa_id, ans.strip()))
                elif isinstance(ans, dict) and ans.get("answer_text", "").strip():
                    cursor.execute("""
                        INSERT INTO qa_answer_variants (qa_id, answer_text, is_primary, language)
                        VALUES (?, ?, ?, ?)
                    """, (
                        qa_id,
                        ans["answer_text"].strip(),
                        ans.get("is_primary", 1),
                        ans.get("language", "bn")
                    ))
            return qa_id

    def get_all_qa_knowledge(self, limit: int = 100) -> list[dict[str, Any]]:
        """Retrieves all Many-to-Many Q&A records with aggregated questions and answers."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM qa_knowledge_base ORDER BY id DESC LIMIT ?
            """, (limit,))
            qa_rows = cursor.fetchall()
            result = []

            for qa in qa_rows:
                qa_id = qa["id"]
                cursor.execute("SELECT question_text FROM qa_question_variants WHERE qa_id = ?", (qa_id,))
                q_vars = [r["question_text"] for r in cursor.fetchall()]

                cursor.execute("SELECT answer_text, is_primary, language FROM qa_answer_variants WHERE qa_id = ? ORDER BY is_primary DESC, id ASC", (qa_id,))
                a_vars = [dict(r) for r in cursor.fetchall()]

                qa_dict = dict(qa)
                qa_dict["question_variants"] = q_vars
                qa_dict["answer_variants"] = a_vars
                qa_dict["primary_answer"] = a_vars[0]["answer_text"] if a_vars else ""
                result.append(qa_dict)

            return result

    def delete_qa_knowledge(self, qa_id: int) -> bool:
        """Deletes a Q&A record and its cascade variants."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM qa_question_variants WHERE qa_id = ?", (qa_id,))
            cursor.execute("DELETE FROM qa_answer_variants WHERE qa_id = ?", (qa_id,))
            cursor.execute("DELETE FROM qa_knowledge_base WHERE id = ?", (qa_id,))
            return cursor.rowcount > 0

    def match_qa_knowledge(self, user_query: str) -> Optional[dict[str, Any]]:
        """
        Fast-path matcher: searches if the user query closely matches any question variant.
        """
        q_clean = user_query.strip().lower()
        if len(q_clean) < 3:
            return None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT v.qa_id, v.question_text, k.category, k.primary_question
                FROM qa_question_variants v
                JOIN qa_knowledge_base k ON v.qa_id = k.id
                WHERE k.is_active = 1
            """)
            all_variants = cursor.fetchall()

            matched_qa_id = None
            for row in all_variants:
                var_text = row["question_text"].strip().lower()
                if var_text == q_clean or var_text in q_clean or q_clean in var_text:
                    matched_qa_id = row["qa_id"]
                    break

            if not matched_qa_id:
                return None

            # Fetch primary or best answer
            cursor.execute("""
                SELECT answer_text, language FROM qa_answer_variants
                WHERE qa_id = ?
                ORDER BY is_primary DESC, id ASC LIMIT 1
            """, (matched_qa_id,))
            ans_row = cursor.fetchone()

            if ans_row:
                return {
                    "qa_id": matched_qa_id,
                    "answer": ans_row["answer_text"],
                    "language": ans_row["language"]
                }
        return None

    # --- Academic Examination Information Management CRUD ---
    @staticmethod
    def _get_program_bengali_name(prog: str) -> str:
        prog_low = str(prog).lower()
        if "honour" in prog_low or "অনার্স" in prog_low:
            return "অনার্স"
        if "degree" in prog_low or "ডিগ্রি" in prog_low or "ডিগ্রী" in prog_low:
            return "ডিগ্রি পাস"
        if "master" in prog_low or "মাস্টার্স" in prog_low or "মাস্টাস" in prog_low:
            return "মাস্টার্স"
        if "pro" in prog_low or "প্রফেশনাল" in prog_low:
            return "প্রফেশনাল"
        return prog

    def upsert_academic_exam_info(self, data: dict[str, Any], user_name: str = "Admin") -> dict[str, Any]:
        """
        Inserts or updates an Academic Examination record.
        Unique identity: (program_type, examination_year, part, semester).
        Ensures examination years (e.g. 2024 vs 2025) are preserved as distinct records.
        """
        program_type = str(data.get("program_type", "Honours")).strip()
        program_type_name = str(data.get("program_type_name") or self._get_program_bengali_name(program_type)).strip()
        course_name = str(data.get("course_name") or "").strip()
        examination_year = str(data.get("examination_year") or data.get("exam_year", "")).strip()
        if not examination_year:
            examination_year = "2025"

        part = str(data.get("part") or data.get("part_or_year", "N/A")).strip()
        if not part or part.lower() in ["none", "null", ""]:
            part = course_name if (program_type.lower() == "professional" and course_name) else "N/A"
        elif program_type.lower() == "professional" and course_name and part.startswith("Part "):
            part = course_name

        semester = str(data.get("semester", "N/A")).strip()
        if not semester or semester.lower() in ["none", "null", ""]:
            semester = "N/A"

        incourse_exam_date = str(data.get("incourse_exam_date") or data.get("incourse_date", "")).strip()
        incourse_marks_deadline = str(data.get("incourse_marks_deadline") or data.get("last_date_incourse_marks", "")).strip()
        form_fillup_start_date = str(data.get("form_fillup_start_date", "")).strip()
        form_fillup_deadline = str(data.get("form_fillup_deadline") or data.get("form_fillup_date", "")).strip()
        exam_date = str(data.get("exam_date", "")).strip()
        routine_publication_date = str(data.get("routine_publication_date") or data.get("routine_url", "")).strip()
        admit_card_date = str(data.get("admit_card_date", "")).strip()
        last_exam_date = str(data.get("last_exam_date") or data.get("last_date_exam", "")).strip()
        practical_marks_start_date = str(data.get("practical_marks_start_date") or data.get("practical_marks_date", "")).strip()
        practical_marks_deadline = str(data.get("practical_marks_deadline") or data.get("last_date_practical_marks", "")).strip()
        probable_result_date = str(data.get("probable_result_date", "")).strip()
        actual_result_date = str(data.get("actual_result_date") or data.get("result_publish_date", "")).strip()
        results_published = "Yes" if str(data.get("results_published", "No")).strip().lower() in ["yes", "true", "1", "হ্যাঁ"] else "No"
        rescrutiny_start_date = str(data.get("rescrutiny_start_date") or data.get("rescrutiny_apply_date", "")).strip()
        rescrutiny_deadline = str(data.get("rescrutiny_deadline", "")).strip()
        rescrutiny_result_date = str(data.get("rescrutiny_result_date", "")).strip()
        document_printing_date = str(data.get("document_printing_date") or data.get("certificate_printing_date", "")).strip()
        documents_printed = "Yes" if str(data.get("documents_printed") or data.get("printed_status", "No")).strip().lower() in ["yes", "true", "1", "হ্যাঁ"] else "No"
        revaluation_result_url = str(data.get("revaluation_result_url") or data.get("revaluation_result_link", "https://results.nu.ac.bd/")).strip()
        college_wise_result_url = str(data.get("college_wise_result_url") or data.get("collegewise_result_link", "http://103.113.200.68/nu-app/search.php")).strip()
        remarks = str(data.get("remarks") or data.get("notes", "")).strip()
        source_url = str(data.get("source_url", "")).strip()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO academic_exam_information (
                    program_type, program_type_name, course_name, examination_year, part, semester,
                    incourse_exam_date, incourse_marks_deadline, form_fillup_start_date, form_fillup_deadline,
                    exam_date, routine_publication_date, admit_card_date, last_exam_date,
                    practical_marks_start_date, practical_marks_deadline, probable_result_date, actual_result_date,
                    results_published, rescrutiny_start_date, rescrutiny_deadline, rescrutiny_result_date,
                    document_printing_date, documents_printed, revaluation_result_url, college_wise_result_url,
                    remarks, source_url, created_by, updated_by, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(program_type, examination_year, part, semester) DO UPDATE SET
                    program_type_name = excluded.program_type_name,
                    course_name = excluded.course_name,
                    incourse_exam_date = excluded.incourse_exam_date,
                    incourse_marks_deadline = excluded.incourse_marks_deadline,
                    form_fillup_start_date = excluded.form_fillup_start_date,
                    form_fillup_deadline = excluded.form_fillup_deadline,
                    exam_date = excluded.exam_date,
                    routine_publication_date = excluded.routine_publication_date,
                    admit_card_date = excluded.admit_card_date,
                    last_exam_date = excluded.last_exam_date,
                    practical_marks_start_date = excluded.practical_marks_start_date,
                    practical_marks_deadline = excluded.practical_marks_deadline,
                    probable_result_date = excluded.probable_result_date,
                    actual_result_date = excluded.actual_result_date,
                    results_published = excluded.results_published,
                    rescrutiny_start_date = excluded.rescrutiny_start_date,
                    rescrutiny_deadline = excluded.rescrutiny_deadline,
                    rescrutiny_result_date = excluded.rescrutiny_result_date,
                    document_printing_date = excluded.document_printing_date,
                    documents_printed = excluded.documents_printed,
                    revaluation_result_url = excluded.revaluation_result_url,
                    college_wise_result_url = excluded.college_wise_result_url,
                    remarks = excluded.remarks,
                    source_url = excluded.source_url,
                    updated_by = excluded.updated_by,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                program_type, program_type_name, course_name, examination_year, part, semester,
                incourse_exam_date, incourse_marks_deadline, form_fillup_start_date, form_fillup_deadline,
                exam_date, routine_publication_date, admit_card_date, last_exam_date,
                practical_marks_start_date, practical_marks_deadline, probable_result_date, actual_result_date,
                results_published, rescrutiny_start_date, rescrutiny_deadline, rescrutiny_result_date,
                document_printing_date, documents_printed, revaluation_result_url, college_wise_result_url,
                remarks, source_url, user_name, user_name
            ))

            # Fetch the updated/inserted record
            cursor.execute("""
                SELECT * FROM academic_exam_information
                WHERE program_type = ? AND examination_year = ? AND part = ? AND semester = ?
            """, (program_type, examination_year, part, semester))
            row = cursor.fetchone()
            return dict(row) if row else {}


    def get_academic_exam_info_by_id(self, record_id: int) -> Optional[dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM academic_exam_information WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def lookup_academic_exam_info(
        self,
        program_type: str,
        examination_year: Optional[str] = None,
        part: Optional[str] = None,
        semester: Optional[str] = None,
        course_name: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Retrieves matching examination records.
        If examination_year is omitted, returns records ordered by examination_year DESC.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM academic_exam_information WHERE LOWER(program_type) = LOWER(?)"
            params = [program_type]

            if course_name and isinstance(course_name, str) and course_name.lower() != "all":
                c_clean = course_name.lower()
                query += " AND (LOWER(course_name) LIKE ? OR LOWER(part) LIKE ? OR LOWER(program_type_name) LIKE ?)"
                params.extend([f"%{c_clean}%", f"%{c_clean}%", f"%{c_clean}%"])
            elif part and isinstance(part, str) and part.lower() != "all":
                p_clean = part.lower()
                query += " AND (LOWER(part) = LOWER(?) OR LOWER(course_name) LIKE ? OR LOWER(part) LIKE ?)"
                params.extend([part, f"%{p_clean}%", f"%{p_clean}%"])

            if semester and isinstance(semester, str) and semester.lower() != "all":
                sem_clean = semester.lower()
                query += " AND (LOWER(semester) = LOWER(?) OR LOWER(semester) LIKE ?)"
                params.extend([semester, f"%{sem_clean}%"])

            if examination_year and isinstance(examination_year, str) and examination_year.lower() != "all":
                query += " AND examination_year = ?"
                params.append(examination_year)

            query += " ORDER BY examination_year DESC, part ASC, semester ASC"
            cursor.execute(query, tuple(params))
            return [dict(r) for r in cursor.fetchall()]

    def list_academic_exam_info(
        self,
        program_type: Optional[str] = None,
        examination_year: Optional[str] = None,
        part: Optional[str] = None,
        semester: Optional[str] = None,
        course_name: Optional[str] = None,
        results_published: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            where_clauses = ["1=1"]
            params = []

            if program_type and isinstance(program_type, str):
                where_clauses.append("LOWER(program_type) = LOWER(?)")
                params.append(program_type)
            if examination_year and isinstance(examination_year, str):
                where_clauses.append("examination_year = ?")
                params.append(examination_year)
            if part and isinstance(part, str) and part.lower() != "all":
                where_clauses.append("LOWER(part) = LOWER(?)")
                params.append(part)
            if semester and isinstance(semester, str) and semester.lower() != "all":
                where_clauses.append("LOWER(semester) = LOWER(?)")
                params.append(semester)
            if course_name and isinstance(course_name, str) and course_name.lower() != "all":
                where_clauses.append("(LOWER(course_name) LIKE ? OR LOWER(part) LIKE ?)")
                params.extend([f"%{course_name.lower()}%", f"%{course_name.lower()}%"])
            if results_published and isinstance(results_published, str):
                where_clauses.append("LOWER(results_published) = LOWER(?)")
                params.append(results_published)
            if search and isinstance(search, str):
                where_clauses.append("(LOWER(course_name) LIKE ? OR examination_year LIKE ? OR remarks LIKE ? OR exam_date LIKE ? OR LOWER(part) LIKE ?)")
                q_term = f"%{search.lower()}%"
                params.extend([q_term, f"%{search}%", f"%{search}%", f"%{search}%", q_term])

            where_str = " AND ".join(where_clauses)
            
            # Count total
            cursor.execute(f"SELECT COUNT(*) as cnt FROM academic_exam_information WHERE {where_str}", tuple(params))
            total_count = cursor.fetchone()["cnt"]

            # Query page
            query_sql = f"""
                SELECT * FROM academic_exam_information
                WHERE {where_str}
                ORDER BY updated_at DESC, examination_year DESC
                LIMIT ? OFFSET ?
            """
            cursor.execute(query_sql, tuple(params + [limit, offset]))
            items = [dict(r) for r in cursor.fetchall()]
            return items, total_count

    def delete_academic_exam_info(self, record_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM academic_exam_information WHERE id = ?", (record_id,))
            return cursor.rowcount > 0

    def get_academic_exam_summary_metadata(self) -> dict[str, Any]:
        """Returns distinct programs, available examination years, and parts in the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT program_type FROM academic_exam_information ORDER BY program_type ASC")
            programs = [r["program_type"] for r in cursor.fetchall()]

            cursor.execute("SELECT DISTINCT examination_year FROM academic_exam_information ORDER BY examination_year DESC")
            years = [r["examination_year"] for r in cursor.fetchall()]

            cursor.execute("SELECT COUNT(*) as total FROM academic_exam_information")
            total = cursor.fetchone()["total"]

            return {
                "available_programs": programs or ["Honours", "Degree Pass", "Master's", "Professional"],
                "available_years": years,
                "total_records": total
            }

    # --- Backwards Compatibility Wrappers for academic_exam_static_info ---
    def upsert_academic_static_info(self, data: dict[str, Any]) -> dict[str, Any]:
        program_type = str(data.get("program_type", "Honours")).strip()
        part_or_year = str(data.get("part_or_year") or data.get("part", "1")).strip()
        exam_year = str(data.get("exam_year") or data.get("examination_year", "")).strip()
        incourse_date = str(data.get("incourse_date") or data.get("incourse_exam_date", "")).strip()
        last_date_incourse_marks = str(data.get("last_date_incourse_marks") or data.get("incourse_marks_deadline", "")).strip()
        form_fillup_date = str(data.get("form_fillup_date") or data.get("form_fillup_deadline", "")).strip()
        exam_date = str(data.get("exam_date", "")).strip()
        routine_url = str(data.get("routine_url") or data.get("routine_publication_date", "")).strip()
        admit_card_date = str(data.get("admit_card_date", "")).strip()
        last_date_exam = str(data.get("last_date_exam") or data.get("last_exam_date", "")).strip()
        practical_marks_date = str(data.get("practical_marks_date") or data.get("practical_marks_start_date", "")).strip()
        last_date_practical_marks = str(data.get("last_date_practical_marks") or data.get("practical_marks_deadline", "")).strip()
        probable_result_date = str(data.get("probable_result_date", "")).strip()
        result_publish_date = str(data.get("result_publish_date") or data.get("actual_result_date", "")).strip()
        results_published = str(data.get("results_published", "No")).strip()
        rescrutiny_apply_date = str(data.get("rescrutiny_apply_date") or data.get("rescrutiny_start_date", "")).strip()
        rescrutiny_result_date = str(data.get("rescrutiny_result_date", "")).strip()
        certificate_printing_date = str(data.get("certificate_printing_date") or data.get("document_printing_date", "")).strip()
        printed_status = str(data.get("printed_status") or data.get("documents_printed", "No")).strip()
        revaluation_result_link = str(data.get("revaluation_result_link") or data.get("revaluation_result_url", "https://results.nu.ac.bd/")).strip()
        collegewise_result_link = str(data.get("collegewise_result_link") or data.get("college_wise_result_url", "http://103.113.200.68/nu-app/search.php")).strip()
        notes = str(data.get("notes") or data.get("remarks", "")).strip()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO academic_exam_static_info (
                    program_type, part_or_year, exam_year, incourse_date, last_date_incourse_marks,
                    form_fillup_date, exam_date, routine_url, admit_card_date, last_date_exam,
                    practical_marks_date, last_date_practical_marks, probable_result_date, result_publish_date,
                    results_published, rescrutiny_apply_date, rescrutiny_result_date, certificate_printing_date,
                    printed_status, revaluation_result_link, collegewise_result_link, notes, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(program_type, part_or_year) DO UPDATE SET
                    exam_year = excluded.exam_year,
                    incourse_date = excluded.incourse_date,
                    last_date_incourse_marks = excluded.last_date_incourse_marks,
                    form_fillup_date = excluded.form_fillup_date,
                    exam_date = excluded.exam_date,
                    routine_url = excluded.routine_url,
                    admit_card_date = excluded.admit_card_date,
                    last_date_exam = excluded.last_date_exam,
                    practical_marks_date = excluded.practical_marks_date,
                    last_date_practical_marks = excluded.last_date_practical_marks,
                    probable_result_date = excluded.probable_result_date,
                    result_publish_date = excluded.result_publish_date,
                    results_published = excluded.results_published,
                    rescrutiny_apply_date = excluded.rescrutiny_apply_date,
                    rescrutiny_result_date = excluded.rescrutiny_result_date,
                    certificate_printing_date = excluded.certificate_printing_date,
                    printed_status = excluded.printed_status,
                    revaluation_result_link = excluded.revaluation_result_link,
                    collegewise_result_link = excluded.collegewise_result_link,
                    notes = excluded.notes,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                program_type, part_or_year, exam_year, incourse_date, last_date_incourse_marks,
                form_fillup_date, exam_date, routine_url, admit_card_date, last_date_exam,
                practical_marks_date, last_date_practical_marks, probable_result_date, result_publish_date,
                results_published, rescrutiny_apply_date, rescrutiny_result_date, certificate_printing_date,
                printed_status, revaluation_result_link, collegewise_result_link, notes
            ))

            cursor.execute("SELECT * FROM academic_exam_static_info WHERE program_type = ? AND part_or_year = ?", (program_type, part_or_year))
            row = cursor.fetchone()
            return dict(row) if row else {}

    def get_academic_static_info(self, program_type: str, part_or_year: Optional[str] = None) -> Optional[dict[str, Any]]:
        # First query new academic_exam_information
        items = self.lookup_academic_exam_info(program_type=program_type, part=part_or_year)
        if items:
            return items[0]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            if part_or_year:
                cursor.execute("SELECT * FROM academic_exam_static_info WHERE LOWER(program_type) = LOWER(?) AND LOWER(part_or_year) = LOWER(?)", (program_type, part_or_year))
            else:
                cursor.execute("SELECT * FROM academic_exam_static_info WHERE LOWER(program_type) = LOWER(?) ORDER BY part_or_year ASC LIMIT 1", (program_type,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_academic_static_info(self, program_type: Optional[str] = None) -> list[dict[str, Any]]:
        items, _ = self.list_academic_exam_info(program_type=program_type, limit=100)
        if items:
            return items
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if program_type:
                cursor.execute("SELECT * FROM academic_exam_static_info WHERE LOWER(program_type) = LOWER(?) ORDER BY part_or_year ASC", (program_type,))
            else:
                cursor.execute("SELECT * FROM academic_exam_static_info ORDER BY program_type ASC, part_or_year ASC")
            return [dict(r) for r in cursor.fetchall()]

    def delete_academic_static_info(self, entry_id: int) -> bool:
        deleted = self.delete_academic_exam_info(entry_id)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM academic_exam_static_info WHERE id = ?", (entry_id,))
            return deleted or (cursor.rowcount > 0)

_sql_store_instance = None

def get_sql_store() -> SQLStore:
    global _sql_store_instance
    if _sql_store_instance is None:
        _sql_store_instance = SQLStore()
    return _sql_store_instance

