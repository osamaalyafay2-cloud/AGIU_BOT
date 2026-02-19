import sqlite3
import os

# =====================================================
# تحديد مسار قاعدة البيانات
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "university.db")

conn = sqlite3.connect(DATABASE)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

# =====================================================
# الجداول الأساسية للنظام الأكاديمي
# =====================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS colleges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    college_id INTEGER NOT NULL,
    FOREIGN KEY(college_id)
        REFERENCES colleges(id)
        ON DELETE CASCADE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS years (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    department_id INTEGER NOT NULL,
    FOREIGN KEY(department_id)
        REFERENCES departments(id)
        ON DELETE CASCADE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    year_id INTEGER NOT NULL,
    FOREIGN KEY(year_id)
        REFERENCES years(id)
        ON DELETE CASCADE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    level_id INTEGER NOT NULL,
    FOREIGN KEY(level_id)
        REFERENCES levels(id)
        ON DELETE CASCADE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS contents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,
    subject_id INTEGER NOT NULL,
    FOREIGN KEY(subject_id)
        REFERENCES subjects(id)
        ON DELETE CASCADE
)
""")

# =====================================================
# نظام المستخدمين والصلاحيات
# =====================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('super_admin','user'))
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS user_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    department_id INTEGER NOT NULL,
    year_id INTEGER NOT NULL,
    level_id INTEGER NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(department_id) REFERENCES departments(id) ON DELETE CASCADE,
    FOREIGN KEY(year_id) REFERENCES years(id) ON DELETE CASCADE,
    FOREIGN KEY(level_id) REFERENCES levels(id) ON DELETE CASCADE
)
""")

# =====================================================
# تحسين الأداء باستخدام Indexes
# =====================================================

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

# =====================================================
# حفظ وإغلاق
# =====================================================

conn.commit()
conn.close()

print("Database created successfully")