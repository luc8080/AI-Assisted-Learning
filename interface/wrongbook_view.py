import streamlit as st
import sqlite3
import pandas as pd
from data_store.question_loader import get_question_by_id
from interface.task_view import run_task_view

DB_PATH = "data_store/user_log.sqlite"

# 取得錯題紀錄
def get_wrong_answers():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT * FROM answer_log
        WHERE is_correct = 0
        ORDER BY timestamp DESC
    """, conn)
    conn.close()
    return df

# 顯示單題詳細內容
def show_question_detail(row):
    st.markdown(f"### 題號：{row['question_id']}")
    question = get_question_by_id(row['question_id'])
    if not question:
        st.warning("查無題目內容")
        return

    st.markdown(f"**題幹：** {question['題幹']}")
    for k, v in question['選項'].items():
        st.markdown(f"({k}) {v}")

    st.markdown(f"✅ 正確答案：{row['correct_answer']}")
    st.markdown(f"🧍‍♂️ 你的答案：{row['student_answer']}")

    if st.button(f"🔁 重新挑戰 {row['question_id']}"):
        st.session_state.from_wrongbook = row["question_id"]
        st.session_state.challenge_mode = True
        st.rerun()

    note = st.text_area("✏️ 加入筆記（可選）：", key=f"note_{row['id']}")
    if st.button("💾 儲存筆記", key=f"save_{row['id']}"):
        st.success("（模擬）筆記已儲存")

# 主錯題本頁面
def run_wrongbook_view():
    # ✅ 若正在挑戰模式，直接載入作答頁
    if st.session_state.get("challenge_mode"):
        run_task_view()
        st.stop()

    st.header("❌ 我的錯題本")
    df = get_wrong_answers()

    if df.empty:
        st.info("目前沒有錯題紀錄，太棒了！")
        return

    st.markdown(f"共 {len(df)} 題錯誤紀錄：")
    selected = st.selectbox("請選擇一題查看：", options=df.index,
                             format_func=lambda i: f"{df.loc[i, 'question_id']}（答：{df.loc[i, 'student_answer']}）")
    show_question_detail(df.loc[selected])