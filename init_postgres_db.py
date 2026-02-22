import os
import psycopg2

# ===============================================
# الاتصال بقاعدة البيانات عبر DATABASE_URL
# ===============================================

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# ===============================================
# الجداول الأساسية للنظام الأكاديمي
# ===============================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS colleges (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    college_id INTEGER NOT NULL,
    FOREIGN KEY (college_id)
        REFERENCES colleges(id)
        ON DELETE CASCADE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS years (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    department_id INTEGER NOT NULL,
    FOREIGN KEY (department_id)
        REFERENCES departments(id)
        ON DELETE CASCADE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS levels (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    year_id INTEGER NOT NULL,
    FOREIGN KEY (year_id)
        REFERENCES years(id)
        ON DELETE CASCADE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS subjects (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    level_id INTEGER NOT NULL,
    FOREIGN KEY (level_id)
        REFERENCES levels(id)
        ON DELETE CASCADE
)
""")

# ✅ تم تعديل الجدول ليعتمد على file_id بدلاً من file_path

cursor.execute("""
CREATE TABLE IF NOT EXISTS contents (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    type TEXT NOT NULL,
    file_id TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,
    subject_id INTEGER NOT NULL,
    FOREIGN KEY (subject_id)
        REFERENCES subjects(id)
        ON DELETE CASCADE
)
""")

# ===============================================
# نظام المستخدمين والصلاحيات
# ===============================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('super_admin','user'))
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS user_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    department_id INTEGER NOT NULL,
    year_id INTEGER NOT NULL,
    level_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE,
    FOREIGN KEY (year_id) REFERENCES years(id) ON DELETE CASCADE,
    FOREIGN KEY (level_id) REFERENCES levels(id) ON DELETE CASCADE
)
""")

# ===============================================
# تحسين الأداء باستخدام Indexes
# ===============================================

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_departments_college
ON departments(college_id)
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_years_department
ON years(department_id)
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_levels_year
ON levels(year_id)
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_subjects_level
ON subjects(level_id)
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_contents_subject
ON contents(subject_id)
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_permissions_user
ON user_permissions(user_id)
""")

# ===============================================
# حفظ وإغلاق
# ===============================================

conn.commit()
cursor.close()
conn.close()

print("PostgreSQL database initialized successfully")