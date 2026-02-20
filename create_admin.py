import os
import psycopg2
from werkzeug.security import generate_password_hash

# قراءة رابط قاعدة البيانات من متغير البيئة
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL is not set")

try:
    # الاتصال بقاعدة البيانات
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    username = "ossama"
    password = "111111"  # غيّرها بعد أول تسجيل دخول

    hashed_password = generate_password_hash(password)

    # إدخال المستخدم إذا لم يكن موجود مسبقًا
    cursor.execute("""
        INSERT INTO users (username, password, role)
        VALUES (%s, %s, %s)
        ON CONFLICT (username) DO NOTHING
    """, (username, hashed_password, "super_admin"))

    conn.commit()

    if cursor.rowcount > 0:
        print("Super admin created successfully")
    else:
        print("Super admin already exists")

except Exception as e:
    print("Error creating super admin:", e)

finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()