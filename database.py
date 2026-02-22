import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in environment variables")

class DBWrapper:
    def __init__(self):
        self.conn = psycopg2.connect(
            DATABASE_URL,
            connect_timeout=5
        )
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)

        # 🔥 إضافة العمود إذا لم يكن موجودًا
        self.cursor.execute("""
            ALTER TABLE contents
            ADD COLUMN IF NOT EXISTS file_id TEXT;
        """)
        self.conn.commit()
    
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