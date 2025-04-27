import sqlite3
import random
import streamlit as st

DB_PATH = "data_store/question_bank.sqlite"

# 取得所有題目 ID
def get_all_question_ids():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM questions")
    results = [row[0] for row in cursor.fetchall()]
    conn.close()
    return results

# 隨機取得一題
def get_random_question():
    # 若來自錯題本，優先載入指定題號
    if "from_wrongbook" in st.session_state:
        qid = st.session_state.pop("from_wrongbook")
        return get_question_by_id(qid)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "題號": row[0],
        "出處": row[1],
        "題幹": row[2],
        "選項": {
            "A": row[3],
            "B": row[4],
            "C": row[5],
            "D": row[6]
        },
        "正解": row[7],
        "主題": row[8],
        "段落標題": row[9],
        "關鍵詞": row[10].split(", ") if row[10] else []
    }

# 依主題出題（可擴充）
def get_questions_by_topic(topic):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions WHERE topic = ?", (topic,))
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "題號": row[0],
            "出處": row[1],
            "題幹": row[2],
            "選項": {
                "A": row[3],
                "B": row[4],
                "C": row[5],
                "D": row[6]
            },
            "正解": row[7],
            "主題": row[8],
            "段落標題": row[9],
            "關鍵詞": row[10].split(", ") if row[10] else []
        }
        for row in rows
    ]

# 根據題號查詢題目
def get_question_by_id(qid: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions WHERE id = ?", (qid,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "題號": row[0],
        "出處": row[1],
        "題幹": row[2],
        "選項": {
            "A": row[3],
            "B": row[4],
            "C": row[5],
            "D": row[6]
        },
        "正解": row[7],
        "主題": row[8],
        "段落標題": row[9],
        "關鍵詞": row[10].split(", ") if row[10] else []
    }
