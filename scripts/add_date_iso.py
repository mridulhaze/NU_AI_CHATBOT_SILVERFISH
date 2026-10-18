import sqlite3
import re
from datetime import datetime
from backend.services.notice_service import parse_notice_date

def add_and_populate_date_iso():
    conn = sqlite3.connect("data/nu_assistant.db")
    c = conn.cursor()

    # Check if date_iso exists
    c.execute("PRAGMA table_info(notices)")
    cols = [r[1] for r in c.fetchall()]
    if "date_iso" not in cols:
        print("Adding column date_iso...")
        c.execute("ALTER TABLE notices ADD COLUMN date_iso TEXT")
        c.execute("CREATE INDEX IF NOT EXISTS idx_notices_date_iso ON notices(date_iso DESC, id DESC)")

    c.execute("SELECT id, title, published_date, url FROM notices WHERE date_iso IS NULL OR date_iso = ''")
    rows = c.fetchall()
    print(f"Populating date_iso for {len(rows)} notices...")

    updates = []
    for r_id, title, pub_date, url in rows:
        dt = parse_notice_date(pub_date, title, url)
        iso_str = dt.strftime("%Y-%m-%d")
        updates.append((iso_str, r_id))

    c.executemany("UPDATE notices SET date_iso = ? WHERE id = ?", updates)
    conn.commit()

    c.execute("SELECT id, title, published_date, date_iso, url FROM notices ORDER BY date_iso DESC, id DESC LIMIT 10")
    print("\nTop 10 Newest Notices in DB:")
    for r in c.fetchall():
        print(f"[{r[3]}] ({r[2]}) {r[1][:70]} -> {r[4]}")

    conn.close()

if __name__ == "__main__":
    add_and_populate_date_iso()
