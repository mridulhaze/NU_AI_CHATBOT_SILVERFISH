import sqlite3
import sys

def fix_swapped_notices():
    conn = sqlite3.connect("data/nu_assistant.db")
    cursor = conn.cursor()

    months = ["january","february","march","april","may","june","july","august","september","october","november","december"]
    clause = " OR ".join([f"LOWER(title) LIKE '%{m}%'" for m in months])

    cursor.execute(f"""
        SELECT id, title, published_date, url
        FROM notices
        WHERE ({clause}) AND LENGTH(published_date) > 10
    """)
    rows = cursor.fetchall()
    print(f"Found {len(rows)} swapped notices to correct.")

    fixed_count = 0
    for row_id, date_str, title_str, url in rows:
        cursor.execute("""
            UPDATE notices
            SET title = ?, published_date = ?, raw_text = ?
            WHERE id = ?
        """, (title_str, date_str, f"Title: {title_str}\nDate: {date_str}\nLink: {url}", row_id))
        fixed_count += 1

    conn.commit()
    conn.close()
    print(f"Successfully corrected {fixed_count} notices in database!")

if __name__ == "__main__":
    fix_swapped_notices()
