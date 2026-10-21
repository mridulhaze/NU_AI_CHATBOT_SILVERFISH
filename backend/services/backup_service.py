import os
import io
import json
import shutil
import zipfile
import hashlib
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("NU_BACKUP_SERVICE")

DATA_DIR = Path("data")
BACKUP_DIR = Path("backups")
TOKENS_DB_PATH = DATA_DIR / "nu_tokens.db"
ASSISTANT_DB_PATH = DATA_DIR / "nu_assistant.db"

class BackupService:
    def __init__(self):
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def _compute_sha256(self, file_path: Path) -> str:
        if not file_path.exists():
            return ""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _get_db_stats(self) -> Dict[str, Any]:
        stats = {
            "tokens_count": 0,
            "users_count": 0,
            "solvers_count": 0,
            "services_count": 0
        }
        if TOKENS_DB_PATH.exists():
            try:
                conn = sqlite3.connect(TOKENS_DB_PATH)
                stats["tokens_count"] = conn.execute("SELECT COUNT(*) FROM token_requests").fetchone()[0]
                stats["users_count"] = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                stats["solvers_count"] = conn.execute("SELECT COUNT(*) FROM token_solvers").fetchone()[0]
                conn.close()
            except Exception as e:
                logger.warning(f"Failed to read token db stats: {e}")

        if ASSISTANT_DB_PATH.exists():
            try:
                conn = sqlite3.connect(ASSISTANT_DB_PATH)
                stats["notices_count"] = conn.execute("SELECT COUNT(*) FROM notices").fetchone()[0]
                stats["faq_count"] = conn.execute("SELECT COUNT(*) FROM faq_entries").fetchone()[0]
                stats["gaps_count"] = conn.execute("SELECT COUNT(*) FROM gap_queue").fetchone()[0]
                conn.close()
            except Exception as e:
                logger.warning(f"Failed to read assistant db stats: {e}")

        return stats

    def create_backup(self) -> Tuple[Path, Dict[str, Any]]:
        """
        Creates a portable, self-contained ZIP archive of all database files and metadata.
        """
        now = datetime.now(timezone.utc)
        timestamp_str = now.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"nu_system_backup_{timestamp_str}.zip"
        backup_path = BACKUP_DIR / backup_filename

        stats = self._get_db_stats()
        meta = {
            "version": "1.0.0",
            "created_at": now.isoformat(),
            "timestamp": timestamp_str,
            "system": "National University Bangladesh AI Assistant",
            "stats": stats,
            "checksums": {
                "nu_tokens.db": self._compute_sha256(TOKENS_DB_PATH),
                "nu_assistant.db": self._compute_sha256(ASSISTANT_DB_PATH)
            }
        }

        # Use memory buffer or temporary sqlite backups to prevent locked file issues
        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Add metadata.json
            zip_file.writestr("metadata.json", json.dumps(meta, indent=2))

            # Backup nu_tokens.db safely
            if TOKENS_DB_PATH.exists():
                tokens_backup_mem = io.BytesIO()
                src_conn = sqlite3.connect(TOKENS_DB_PATH)
                dest_conn = sqlite3.connect(":memory:")
                src_conn.backup(dest_conn)
                src_conn.close()
                
                # Write memory sqlite to bytes
                temp_file = BACKUP_DIR / f"_temp_tokens_{timestamp_str}.db"
                temp_conn = sqlite3.connect(temp_file)
                dest_conn.backup(temp_conn)
                dest_conn.close()
                temp_conn.close()

                zip_file.write(temp_file, arcname="nu_tokens.db")
                if temp_file.exists():
                    temp_file.unlink()

            # Backup nu_assistant.db safely
            if ASSISTANT_DB_PATH.exists():
                temp_file2 = BACKUP_DIR / f"_temp_assistant_{timestamp_str}.db"
                src_conn2 = sqlite3.connect(ASSISTANT_DB_PATH)
                dest_conn2 = sqlite3.connect(temp_file2)
                src_conn2.backup(dest_conn2)
                src_conn2.close()
                dest_conn2.close()

                zip_file.write(temp_file2, arcname="nu_assistant.db")
                if temp_file2.exists():
                    temp_file2.unlink()

        logger.info(f"Backup created successfully: {backup_path} ({stats})")
        return backup_path, meta

    def list_backups(self) -> List[Dict[str, Any]]:
        """
        Lists all available backups in the backups/ directory.
        """
        backups = []
        if not BACKUP_DIR.exists():
            return []

        for p in BACKUP_DIR.glob("nu_system_backup_*.zip"):
            try:
                stat = p.stat()
                meta = {}
                with zipfile.ZipFile(p, "r") as zf:
                    if "metadata.json" in zf.namelist():
                        meta = json.loads(zf.read("metadata.json").decode("utf-8"))
                
                backups.append({
                    "filename": p.name,
                    "filepath": str(p.absolute()),
                    "size_bytes": stat.st_size,
                    "size_display": f"{stat.st_size / (1024*1024):.2f} MB" if stat.st_size > 1024*1024 else f"{stat.st_size / 1024:.1f} KB",
                    "created_at": meta.get("created_at", datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()),
                    "stats": meta.get("stats", {}),
                    "version": meta.get("version", "1.0.0")
                })
            except Exception as e:
                logger.warning(f"Could not read backup file {p.name}: {e}")

        # Sort by creation descending
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups

    def restore_backup(self, zip_content: bytes, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Validates, creates a safety restore point, and restores databases from uploaded ZIP.
        """
        now = datetime.now(timezone.utc)
        safety_point = BACKUP_DIR / f"_safety_restore_point_{now.strftime('%Y%m%d_%H%M%S')}"
        safety_point.mkdir(parents=True, exist_ok=True)

        # 1. Inspect and validate zip content
        try:
            zip_buffer = io.BytesIO(zip_content)
            with zipfile.ZipFile(zip_buffer, "r") as zf:
                namelist = zf.namelist()
                if "metadata.json" not in namelist or "nu_tokens.db" not in namelist:
                    raise ValueError("Invalid backup archive: missing metadata.json or nu_tokens.db.")
                
                meta = json.loads(zf.read("metadata.json").decode("utf-8"))

                # 2. Create safety snapshot of current databases
                if TOKENS_DB_PATH.exists():
                    shutil.copy2(TOKENS_DB_PATH, safety_point / "nu_tokens.db")
                if ASSISTANT_DB_PATH.exists():
                    shutil.copy2(ASSISTANT_DB_PATH, safety_point / "nu_assistant.db")

                # 3. Extract and replace databases
                extract_temp = safety_point / "extracted"
                extract_temp.mkdir(parents=True, exist_ok=True)
                zf.extractall(extract_temp)

                def _safe_replace_db(src_file: Path, dest_file: Path):
                    try:
                        shutil.copy2(src_file, dest_file)
                    except Exception:
                        s_c = sqlite3.connect(src_file)
                        d_c = sqlite3.connect(dest_file)
                        s_c.backup(d_c)
                        s_c.close()
                        d_c.close()

                if (extract_temp / "nu_tokens.db").exists():
                    _safe_replace_db(extract_temp / "nu_tokens.db", TOKENS_DB_PATH)
                if (extract_temp / "nu_assistant.db").exists():
                    _safe_replace_db(extract_temp / "nu_assistant.db", ASSISTANT_DB_PATH)

                # 4. Verify integrity of newly restored databases
                tokens_ok = True
                conn1 = sqlite3.connect(TOKENS_DB_PATH)
                check1 = conn1.execute("PRAGMA integrity_check").fetchone()[0]
                conn1.close()
                if check1 != "ok":
                    tokens_ok = False

                if not tokens_ok:
                    # Rollback
                    if (safety_point / "nu_tokens.db").exists():
                        shutil.copy2(safety_point / "nu_tokens.db", TOKENS_DB_PATH)
                    raise ValueError(f"Restored database failed integrity check: {check1}. Rolled back.")

                # If uploaded file has a name, also persist it in backups directory
                if filename:
                    persisted_path = BACKUP_DIR / filename
                    if not persisted_path.exists():
                        with open(persisted_path, "wb") as pf:
                            pf.write(zip_content)

                current_stats = self._get_db_stats()
                logger.info(f"System successfully restored from backup. Stats: {current_stats}")
                return {
                    "success": True,
                    "message": "System successfully restored from portable backup file.",
                    "restored_at": now.isoformat(),
                    "backup_metadata": meta,
                    "current_stats": current_stats
                }

        except Exception as e:
            logger.error(f"Restore failed: {e}", exc_info=True)
            # Attempt rollback if safety copies exist
            if (safety_point / "nu_tokens.db").exists():
                shutil.copy2(safety_point / "nu_tokens.db", TOKENS_DB_PATH)
            if (safety_point / "nu_assistant.db").exists():
                shutil.copy2(safety_point / "nu_assistant.db", ASSISTANT_DB_PATH)
            raise ValueError(f"Backup restoration failed: {str(e)}")

_backup_service_instance: Optional[BackupService] = None

def get_backup_service() -> BackupService:
    global _backup_service_instance
    if _backup_service_instance is None:
        _backup_service_instance = BackupService()
    return _backup_service_instance
