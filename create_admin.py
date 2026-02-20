import os
import psycopg2
from werkzeug.security import generate_password_hash

DATABASE_URL = os.environ.get("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

username = "ossama"
password = "111111"   # غيّرها بعد أول تسجيل دخول

hashed_password = generate_password_hash(password)

cursor.execute("""
    INSERT INTO users (username, password, role)
    VALUES (%s, %s, %s)
""", (username, hashed_password, "super_admin"))

conn.commit()
cursor.close()
conn.close()

print("Super admin created successfully")