import sqlite3
import json
from pathlib import Path

def load_questions_from_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def insert_questions_to_db(json_path, sqlite_path="data_store/question_bank.sqlite"):
    questions = load_questions_from_json(json_path)
    Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()

    cursor.execute("""
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
        )
    """)

    for q in questions:
        choices = q.get("選項", {})
        cursor.execute("""
            INSERT OR REPLACE INTO questions (
                id, source, stem, option_a, option_b, option_c, option_d,
                answer, topic, paragraph, keywords
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            q.get("題號"),
            q.get("出處"),
            q.get("題幹"),
            choices.get("A", ""),
            choices.get("B", ""),
            choices.get("C", ""),
            choices.get("D", ""),
            q.get("正解", ""),
            q.get("主題", ""),
            q.get("段落標題", ""),
            ", ".join(q.get("關鍵詞", []))
        ))

    conn.commit()
    conn.close()
    print(f"✅ 已將 {len(questions)} 題匯入資料庫：{sqlite_path}")

# 範例用法
if __name__ == "__main__":
    insert_questions_to_db("data_store/114_國綜.json")
