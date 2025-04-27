-- 建立 answer_log 作答紀錄表
CREATE TABLE IF NOT EXISTS answer_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    question_id TEXT NOT NULL,
    student_answer TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    is_correct INTEGER NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- 建立 questions 題庫資料表
CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,
    source TEXT,
    stem TEXT,
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    answer TEXT,
    topic TEXT,
    paragraph TEXT,
    keywords TEXT
);

-- 建立 users 使用者表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('student', 'teacher', 'admin'))
);

-- 插入預設帳號（若不存在）
INSERT OR IGNORE INTO users (username, password_hash, role) VALUES
('student1', '$2b$12$6MTe9X/WWTJ4PRzO6mVncO.kAKiJ0JHExMJACknNF3BKMK7M0E4J6', 'student'), -- 密碼：123456
('teacher1', '$2b$12$6MTe9X/WWTJ4PRzO6mVncO.kAKiJ0JHExMJACknNF3BKMK7M0E4J6', 'teacher'), -- 密碼：123456
('admin',    '$2b$12$9b2eYfZm0gpD2MyY5vWXRO0R7ylH0aTUN.ZD7uCdaRxzBlqz6W03S', 'admin');    -- 密碼：adminpass
