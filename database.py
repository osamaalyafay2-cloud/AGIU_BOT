import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in environment variables")


class DBWrapper:
    def __init__(self):
        print("🔎 Connecting to DB:", DATABASE_URL.split("@")[-1])

        self.conn = psycopg2.connect(
            DATABASE_URL,
            connect_timeout=5
        )
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)

        # ==========================================
        # فحص بنية جدول contents
        # ==========================================

        self.cursor.execute("""
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'contents'
        """)
        columns = self.cursor.fetchall()

        print("📦 contents structure:", columns)

        column_names = [col["column_name"] for col in columns]

        # ==========================================
        # إضافة file_id إذا لم يكن موجودًا
        # ==========================================

        if "file_id" not in column_names:
            print("➕ Adding file_id column...")
            self.cursor.execute("""
                ALTER TABLE contents
                ADD COLUMN file_id TEXT;
            """)
            self.conn.commit()

        # ==========================================
        # إذا كان file_path موجودًا ومفروض NOT NULL
        # نجعله NULLABLE حتى لا يسبب أخطاء
        # ==========================================

        for col in columns:
            if col["column_name"] == "file_path" and col["is_nullable"] == "NO":
                print("⚠ Removing NOT NULL from file_path...")
                self.cursor.execute("""
                    ALTER TABLE contents
                    ALTER COLUMN file_path DROP NOT NULL;
                """)
                self.conn.commit()

    # ==========================================
    # وظائف التنفيذ
    # ==========================================

    def execute(self, query, params=None):
        self.cursor.execute(query, params or ())
        return self

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc:
            self.conn.rollback()
        else:
            self.conn.commit()
        self.close()


def get_db():
    return DBWrapper()