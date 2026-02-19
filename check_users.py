import sqlite3

conn = sqlite3.connect("university.db")
conn.row_factory = sqlite3.Row

users = conn.execute("SELECT id, username, password, role FROM users").fetchall()

for u in users:
    print(u["id"], u["username"], u["password"], u["role"])

conn.close()