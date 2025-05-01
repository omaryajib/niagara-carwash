import sqlite3

conn = sqlite3.connect("users.db")  # wala "database.db" ila db dyalk smitha haka
c = conn.cursor()
c.execute("SELECT * FROM users")
print(c.fetchall())
conn.close()
