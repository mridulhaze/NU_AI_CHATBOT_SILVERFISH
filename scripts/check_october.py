import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('data/nu_assistant.db')
c = conn.cursor()
c.execute("SELECT id, title, published_date, url FROM notices WHERE published_date LIKE '%October%2026%' ORDER BY id DESC LIMIT 10")
rows = c.fetchall()
print(f"Total October 2026 notices found: {len(rows)}")
for r in rows:
    print(r)
