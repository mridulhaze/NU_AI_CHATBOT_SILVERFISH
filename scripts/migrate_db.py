import sqlite3
from pathlib import Path

db_path = Path("data/nu_assistant.db")
conn = sqlite3.connect(str(db_path))

stmts = [
    "ALTER TABLE academic_exam_information ADD COLUMN course_name TEXT DEFAULT '';",
    "ALTER TABLE faq_entries ADD COLUMN source_key TEXT;",
    "ALTER TABLE faq_entries ADD COLUMN keywords TEXT DEFAULT '';",
    "ALTER TABLE faq_entries ADD COLUMN source_file TEXT DEFAULT 'FAQ/faq.txt';",
    "ALTER TABLE faq_entries ADD COLUMN source_hash TEXT;",
    "ALTER TABLE faq_entries ADD COLUMN likes_count INTEGER DEFAULT 0;",
    "ALTER TABLE faq_entries ADD COLUMN is_active INTEGER DEFAULT 1;",
    """
    CREATE TABLE IF NOT EXISTS faq_likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        faq_id INTEGER NOT NULL,
        session_id TEXT NOT NULL,
        liked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(faq_id, session_id),
        FOREIGN KEY (faq_id) REFERENCES faq_entries(id) ON DELETE CASCADE
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_faq_likes_count ON faq_entries(likes_count DESC);",
    "CREATE INDEX IF NOT EXISTS idx_faq_category_idx ON faq_entries(category);",
    "CREATE INDEX IF NOT EXISTS idx_faq_source_hash ON faq_entries(source_hash);",
    "CREATE INDEX IF NOT EXISTS idx_faq_likes_faq_id ON faq_likes(faq_id);",
    "CREATE INDEX IF NOT EXISTS idx_faq_likes_session ON faq_likes(session_id);"
]

for stmt in stmts:
    try:
        conn.execute(stmt)
        conn.commit()
    except Exception as e:
        print("Note on stmt:", e)

conn.close()
print("Migration completed.")
