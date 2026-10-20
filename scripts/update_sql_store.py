import sys
from pathlib import Path

sql_store_path = Path("db/sql_store.py")
code = sql_store_path.read_text(encoding="utf-8")

old_init = """            with self._get_connection() as conn:
                conn.executescript(schema_sql)
                try:
                    conn.execute("ALTER TABLE academic_exam_information ADD COLUMN course_name TEXT DEFAULT '';")
                    conn.commit()
                except Exception:
                    pass"""

new_init = """            with self._get_connection() as conn:
                conn.executescript(schema_sql)
                for alter_stmt in [
                    "ALTER TABLE academic_exam_information ADD COLUMN course_name TEXT DEFAULT '';",
                    "ALTER TABLE faq_entries ADD COLUMN source_key TEXT;",
                    "ALTER TABLE faq_entries ADD COLUMN keywords TEXT DEFAULT '';",
                    "ALTER TABLE faq_entries ADD COLUMN source_file TEXT DEFAULT 'FAQ/faq.txt';",
                    "ALTER TABLE faq_entries ADD COLUMN source_hash TEXT;",
                    "ALTER TABLE faq_entries ADD COLUMN likes_count INTEGER DEFAULT 0;",
                    "ALTER TABLE faq_entries ADD COLUMN is_active INTEGER DEFAULT 1;",
                ]:
                    try:
                        conn.execute(alter_stmt)
                        conn.commit()
                    except Exception:
                        pass
                try:
                    conn.execute(\"\"\"
                        CREATE TABLE IF NOT EXISTS faq_likes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            faq_id INTEGER NOT NULL,
                            session_id TEXT NOT NULL,
                            liked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(faq_id, session_id),
                            FOREIGN KEY (faq_id) REFERENCES faq_entries(id) ON DELETE CASCADE
                        );
                    \"\"\")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_faq_likes_count ON faq_entries(likes_count DESC);")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_faq_category_idx ON faq_entries(category);")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_faq_source_hash ON faq_entries(source_hash);")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_faq_likes_faq_id ON faq_likes(faq_id);")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_faq_likes_session ON faq_likes(session_id);")
                    conn.commit()
                except Exception:
                    pass"""

if old_init in code:
    code = code.replace(old_init, new_init, 1)

faq_methods = '''

    # --- FAQ Forum & Knowledge Methods ---
    def upsert_faq_record(
        self,
        question: str,
        answer: str,
        category: str = "General",
        source_key: str = "",
        keywords: str = "",
        source_file: str = "FAQ/faq.txt",
        source_hash: Optional[str] = None,
        is_active: int = 1
    ) -> int:
        if not source_hash:
            source_hash = self.compute_hash(f"{question.strip()}|{answer.strip()}")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM faq_entries WHERE source_hash = ?", (source_hash,))
            row = cursor.fetchone()
            if row:
                cursor.execute("""
                    UPDATE faq_entries
                    SET question = ?, answer = ?, category = ?, source_key = ?, keywords = ?, source_file = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (question.strip(), answer.strip(), category.strip(), source_key.strip(), keywords.strip(), source_file, is_active, row["id"]))
                return row["id"]
            else:
                cursor.execute("""
                    INSERT INTO faq_entries (source_key, question, answer, category, keywords, source_file, source_hash, likes_count, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
                """, (source_key.strip(), question.strip(), answer.strip(), category.strip(), keywords.strip(), source_file, source_hash, is_active))
                return cursor.lastrowid

    def get_faq_by_id(self, faq_id: int, session_id: Optional[str] = None) -> Optional[dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM faq_entries WHERE id = ?", (faq_id,))
            row = cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            res["has_liked"] = False
            if session_id:
                cursor.execute("SELECT 1 FROM faq_likes WHERE faq_id = ? AND session_id = ?", (faq_id, session_id))
                if cursor.fetchone():
                    res["has_liked"] = True
            return res

    def list_faqs(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        sort: str = "most_liked",
        limit: int = 30,
        offset: int = 0,
        session_id: Optional[str] = None
    ) -> dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            where_clauses = ["is_active = 1"]
            params: list[Any] = []

            if category and category.strip() and category.strip().lower() != "all":
                where_clauses.append("category = ?")
                params.append(category.strip())

            if search and search.strip():
                s = f"%{search.strip()}%"
                where_clauses.append("(question LIKE ? OR answer LIKE ? OR keywords LIKE ?)")
                params.extend([s, s, s])

            where_sql = " AND ".join(where_clauses)

            # Count total
            cursor.execute(f"SELECT COUNT(*) as cnt FROM faq_entries WHERE {where_sql}", params)
            total = cursor.fetchone()["cnt"]

            # Order by
            if sort == "most_liked":
                order_sql = "ORDER BY likes_count DESC, id ASC"
            elif sort == "latest":
                order_sql = "ORDER BY id DESC"
            else:
                order_sql = "ORDER BY id ASC"

            query_sql = f"SELECT * FROM faq_entries WHERE {where_sql} {order_sql} LIMIT ? OFFSET ?"
            exec_params = list(params)
            exec_params.extend([limit, offset])
            cursor.execute(query_sql, exec_params)
            rows = cursor.fetchall()

            liked_ids = set()
            if session_id and rows:
                faq_ids = [r["id"] for r in rows]
                placeholders = ",".join(["?"] * len(faq_ids))
                cursor.execute(f"SELECT faq_id FROM faq_likes WHERE session_id = ? AND faq_id IN ({placeholders})", [session_id] + faq_ids)
                liked_ids = {r["faq_id"] for r in cursor.fetchall()}

            items = []
            for r in rows:
                item = dict(r)
                item["has_liked"] = item["id"] in liked_ids
                items.append(item)

            return {"total": total, "items": items, "limit": limit, "offset": offset}

    def get_top_liked_faqs(self, limit: int = 10, session_id: Optional[str] = None) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM faq_entries WHERE is_active = 1 ORDER BY likes_count DESC, id ASC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            liked_ids = set()
            if session_id and rows:
                faq_ids = [r["id"] for r in rows]
                placeholders = ",".join(["?"] * len(faq_ids))
                cursor.execute(f"SELECT faq_id FROM faq_likes WHERE session_id = ? AND faq_id IN ({placeholders})", [session_id] + faq_ids)
                liked_ids = {r["faq_id"] for r in cursor.fetchall()}
            items = []
            for r in rows:
                item = dict(r)
                item["has_liked"] = item["id"] in liked_ids
                items.append(item)
            return items

    def get_faq_categories(self) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM faq_entries 
                WHERE is_active = 1 
                GROUP BY category 
                ORDER BY count DESC
            """)
            return [dict(r) for r in cursor.fetchall()]

    def toggle_faq_like(self, faq_id: int, session_id: str) -> dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM faq_entries WHERE id = ?", (faq_id,))
            if not cursor.fetchone():
                return {"error": "FAQ entry not found", "status": 404}

            cursor.execute("SELECT id FROM faq_likes WHERE faq_id = ? AND session_id = ?", (faq_id, session_id))
            existing_like = cursor.fetchone()
            if existing_like:
                cursor.execute("DELETE FROM faq_likes WHERE faq_id = ? AND session_id = ?", (faq_id, session_id))
                cursor.execute("UPDATE faq_entries SET likes_count = MAX(0, likes_count - 1), updated_at = CURRENT_TIMESTAMP WHERE id = ?", (faq_id,))
                has_liked = False
            else:
                cursor.execute("INSERT INTO faq_likes (faq_id, session_id) VALUES (?, ?)", (faq_id, session_id))
                cursor.execute("UPDATE faq_entries SET likes_count = likes_count + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (faq_id,))
                has_liked = True

            cursor.execute("SELECT likes_count FROM faq_entries WHERE id = ?", (faq_id,))
            new_count = cursor.fetchone()["likes_count"]
            conn.commit()
            return {"faq_id": faq_id, "likes_count": new_count, "has_liked": has_liked}
'''

if "def list_faqs" not in code:
    target_anchor = "            return [dict(row) for row in cursor.fetchall()]"
    idx = code.find("def search_faqs")
    ret_idx = code.find(target_anchor, idx)
    insert_pos = ret_idx + len(target_anchor)
    code = code[:insert_pos] + faq_methods + code[insert_pos:]

sql_store_path.write_text(code, encoding="utf-8")
print("Successfully updated db/sql_store.py")
