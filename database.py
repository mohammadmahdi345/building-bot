# database.py

import sqlite3

DB_NAME = "users.db"


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        self.cur = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            unit TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        self.conn.commit()

    def add_user(self, user_id, first_name, last_name, username, unit):
        self.cur.execute("""
        INSERT OR REPLACE INTO users(
            user_id, first_name, last_name, username, unit
        )
        VALUES(?,?,?,?,?)
        """, (user_id, first_name, last_name, username, unit))
        self.conn.commit()

    def user_exists(self, user_id):
        self.cur.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,))
        return self.cur.fetchone() is not None

    def get_unit(self, user_id):
        self.cur.execute("SELECT unit FROM users WHERE user_id=?", (user_id,))
        row = self.cur.fetchone()
        return row[0] if row else None