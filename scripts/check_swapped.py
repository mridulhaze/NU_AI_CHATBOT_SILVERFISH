import sqlite3

conn = sqlite3.connect('data/nu_assistant.db')
c = conn.cursor()
c.execute('SELECT count(*) FROM notices')
total = c.fetchone()[0]

months = ['January','February','March','April','May','June','July','August','September','October','November','December']
clause = ' OR '.join([f"title LIKE '%{m}%'" for m in months])
c.execute(f"SELECT count(*) FROM notices WHERE {clause}")
swapped = c.fetchone()[0]

print(f"Total notices: {total}")
print(f"Swapped notices (where title is a date): {swapped}")
