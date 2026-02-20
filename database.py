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


def get_db():
    return DBWrapper()