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
            phone TEXT,
            unit TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS groups(
            chat_id INTEGER PRIMARY KEY
        )
        """)


        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS settings(
            name TEXT PRIMARY KEY,
            value TEXT
        )
        """)

        self.conn.commit()

    # مرحله 1: ذخیره شماره
    def add_phone(self, user_id, first_name, last_name, username, phone):
        self.cur.execute("""
        INSERT OR REPLACE INTO users(
            user_id, first_name, last_name, username, phone, unit
        )
        VALUES(?,?,?,?,?,NULL)
        """, (user_id, first_name, last_name, username, phone))
        self.conn.commit()

    # مرحله 2: آپدیت واحد
    def update_unit(self, user_id, unit):
        self.cur.execute("""
        UPDATE users
        SET unit=?
        WHERE user_id=?
        """, (unit, user_id))
        self.conn.commit()

    def user_exists(self, user_id):
        self.cur.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,))
        return self.cur.fetchone() is not None

    def get_unit(self, user_id):
        self.cur.execute("SELECT unit FROM users WHERE user_id=?", (user_id,))
        row = self.cur.fetchone()
        return row[0] if row else None

    def get_phone(self, user_id):
        self.cur.execute("SELECT phone FROM users WHERE user_id=?", (user_id,))
        row = self.cur.fetchone()
        return row[0] if row else None

    # برای پنل ادمین
    def get_all_users(self):
        self.cur.execute("SELECT * FROM users")
        return self.cur.fetchall()

    # ذخیره گروه‌هایی که بات داخل آن‌هاست
    def add_group(self, chat_id):
        self.cur.execute(
            "INSERT OR IGNORE INTO groups(chat_id) VALUES(?)",
            (chat_id,)
        )
        self.conn.commit()

    # دریافت همه گروه‌ها
    def get_groups(self):
        self.cur.execute("SELECT chat_id FROM groups")
        return [row[0] for row in self.cur.fetchall()]
    
    def get_show_unit(self):
        self.cur.execute(
            "SELECT value FROM settings WHERE name='show_unit'"
        )

        row = self.cur.fetchone()

        if row is None:
            self.cur.execute(
                "INSERT INTO settings(name,value) VALUES('show_unit','1')"
            )
            self.conn.commit()
            return True

        return row[0] == "1"


    def set_show_unit(self, value):
        self.cur.execute("""
        INSERT OR REPLACE INTO settings(name,value)
        VALUES('show_unit',?)
        """, ("1" if value else "0",))

        self.conn.commit()