import sqlite3
import bcrypt

DB_PATH = "data_store/user_log.sqlite"

def initialize_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 建立 users 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student', 'teacher', 'admin'))
        )
    """)

    # 正確使用 bcrypt 加密生成密碼 hash
    def hash_password(plain_text_password):
        return bcrypt.hashpw(plain_text_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    student_hash = hash_password("123456")
    teacher_hash = hash_password("123456")
    admin_hash = hash_password("adminpass")

    # 插入預設帳號
    cursor.execute("""
        INSERT OR IGNORE INTO users (username, password_hash, role) VALUES
        ('student1', ?, 'student'),
        ('teacher1', ?, 'teacher'),
        ('admin', ?, 'admin')
    """, (student_hash, teacher_hash, admin_hash))

    # 建立 answer_log 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answer_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_id INTEGER,
            question_id TEXT,
            student_answer TEXT,
            correct_answer TEXT,
            is_correct INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅ 資料庫初始化完成")

if __name__ == "__main__":
    initialize_database()
