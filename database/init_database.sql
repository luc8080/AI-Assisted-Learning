\-- 檔案路徑：learning\_assistant/database/init\_database.sql

\-- 題組主表 (閱讀文本)
CREATE TABLE IF NOT EXISTS question\_groups (
id INTEGER PRIMARY KEY AUTOINCREMENT,
title TEXT,
reading\_text TEXT,
category TEXT
);

\-- 子題/單題表
CREATE TABLE IF NOT EXISTS questions (
id INTEGER PRIMARY KEY AUTOINCREMENT,
group\_id INTEGER,
content TEXT NOT NULL,
answer TEXT,
explanation TEXT,
topic TEXT,
difficulty INTEGER,
question\_type TEXT,
FOREIGN KEY(group\_id) REFERENCES question\_groups(id)
);

\-- 其餘用戶與錯題表
CREATE TABLE IF NOT EXISTS users (
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT NOT NULL UNIQUE,
password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS wrongbook (
id INTEGER PRIMARY KEY AUTOINCREMENT,
user\_id INTEGER,
question\_id INTEGER,
note TEXT,
FOREIGN KEY(user\_id) REFERENCES users(id),
FOREIGN KEY(question\_id) REFERENCES questions(id)
);
