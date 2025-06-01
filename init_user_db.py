import sqlite3
import os
import bcrypt

def create_user_database(db_path):
    if os.path.exists(db_path):
        print(f"用戶資料庫已存在：{db_path}")
        return
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL
                )''')
    c.execute('''CREATE TABLE answer_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    user_id INTEGER,
                    question_id TEXT,
                    student_answer TEXT,
                    correct_answer TEXT,
                    is_correct INTEGER,
                    group_id INTEGER,
                    sub_id INTEGER
                )''')
    users = [
        ("student1", "student123", "student"),
        ("teacher1", "teacher123", "teacher"),
        ("admin1", "admin123", "admin"),
    ]
    for username, pw, role in users:
        pw_hash = bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (username, pw_hash, role))
    conn.commit()
    conn.close()
    print(f"用戶資料庫建立完成，已加入 bcrypt 預設帳密：{db_path}")

if __name__ == "__main__":
    db_path = "data_store/user_log.sqlite"
    create_user_database(db_path)
