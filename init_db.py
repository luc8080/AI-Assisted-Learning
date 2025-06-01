# 檔案路徑：learning_assistant/init_db.py

import sqlite3
import os

def create_database(db_path):
    if os.path.exists(db_path):
        print(f"資料庫已存在：{db_path}")
        return
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # 題組主表
    c.execute('''CREATE TABLE question_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    reading_text TEXT,
                    category TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')
    # 子題/單題表
    c.execute('''CREATE TABLE questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER,
                    content TEXT NOT NULL,
                    options TEXT,             -- 選項 (json)
                    answer TEXT,              -- 正解
                    explanation TEXT,         -- 詳細解析
                    topic TEXT,               -- 主題
                    difficulty INTEGER,       -- 難度
                    question_type TEXT,       -- 單選/複選/簡答...
                    paragraph TEXT,           -- 題目專屬閱讀素材
                    keywords TEXT,            -- AI產生關鍵詞
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(group_id) REFERENCES question_groups(id)
                )''')
    # （可選）用戶表 - 建議遷移到 user_log.sqlite
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL
                )''')
    # 錯題本（可選）
    c.execute('''CREATE TABLE IF NOT EXISTS wrongbook (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    question_id INTEGER,
                    note TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(question_id) REFERENCES questions(id)
                )''')
    conn.commit()
    conn.close()
    print(f"資料庫建立完成：{db_path}")

if __name__ == "__main__":
    db_path = "data_store/question_bank.sqlite"
    create_database(db_path)
