import sqlite3
import random

DB_PATH = "data_store/question_bank.sqlite"
USER_LOG_PATH = "data_store/user_log.sqlite"

# === 推薦再練題目 ===
def recommend_next_question_by_topic():
    # 從 user_log 抓取最近錯題的主題
    conn = sqlite3.connect(USER_LOG_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT question_id FROM answer_log
        WHERE is_correct = 0
        ORDER BY timestamp DESC
        LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None  # 沒有錯題紀錄

    recent_qid = row[0]

    # 取得該題主題
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT topic FROM questions WHERE id = ?", (recent_qid,))
    topic_row = cursor.fetchone()
    if not topic_row:
        return None

    topic = topic_row[0]

    # 推薦同主題但不同題號的題目
    cursor.execute("""
        SELECT * FROM questions
        WHERE topic = ? AND id != ?
        ORDER BY RANDOM()
        LIMIT 1
    """, (topic, recent_qid))
    question = cursor.fetchone()
    conn.close()

    if not question:
        return None

    return {
        "題號": question[0],
        "出處": question[1],
        "題幹": question[2],
        "選項": {
            "A": question[3],
            "B": question[4],
            "C": question[5],
            "D": question[6]
        },
        "正解": question[7],
        "主題": question[8],
        "段落標題": question[9],
        "關鍵詞": question[10].split(", ") if question[10] else []
    }
