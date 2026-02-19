import sqlite3
import os

# ======================================================
# تحديد مسار قاعدة البيانات
# ======================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "university.db")

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# ======================================================
# إضافة عمود telegram_id إذا لم يكن موجود
# ======================================================

try:
    cursor.execute("ALTER TABLE users ADD COLUMN telegram_id INTEGER")
    print("Column telegram_id added successfully.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower():
        print("Column telegram_id already exists.")
    else:
        print("Error adding column:", e)

# ======================================================
# إنشاء Unique Index على telegram_id
# ======================================================

try:
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_telegram_id
        ON users(telegram_id)
    """)
    print("Unique index created successfully.")
except Exception as e:
    print("Error creating unique index:", e)

# ======================================================
# حفظ وإغلاق
# ======================================================

conn.commit()
conn.close()

print("Database update finished.")