import streamlit as st
import sqlite3
import json
from models.student_model import StudentModel
from assistant_core.coach.coach_agents import guide_agent, diagnose_agent, extend_agent
from data_store.question_loader import get_question_by_id
from agents import Runner
import asyncio

# === 取得最近錯題題號 ===
def get_recent_wrong_qids(limit=10):
    conn = sqlite3.connect("data_store/user_log.sqlite")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT question_id FROM answer_log
        WHERE is_correct = 0
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [str(row[0]) for row in rows]

# === 取得該題的學生作答與正解 ===
def get_student_answer_and_truth(qid):
    conn = sqlite3.connect("data_store/user_log.sqlite")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT student_answer, correct_answer FROM answer_log
        WHERE question_id = ? ORDER BY timestamp DESC LIMIT 1
    """, (qid,))
    row = cursor.fetchone()
    conn.close()
    return row if row else (None, None)

# === UI ===
def run_coach_chat_view():
    st.title("🧑‍🏫 AI 教練互動")
    st.markdown("請輸入你對某一題的疑問、錯誤原因或想請教 AI 老師的地方 👇")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # 教練風格選擇
    style = st.selectbox("教練回應風格：", ["🧭 引導式（預設）", "🔍 診斷式", "📚 延伸補充"])

    # 題目選擇（包含最近錯題）
    recent_wrong_qids = get_recent_wrong_qids()
    options = [""] + recent_wrong_qids
    selected_qid = st.selectbox("（可選）從最近錯題選擇要討論的題號：", options=options)

    with st.form("chat_form"):
        user_input = st.text_area("你想問什麼？", height=150)
        submitted = st.form_submit_button("送出問題")

    if submitted and user_input.strip():
        # 題目上下文（如有）
        qtext = ""
        if selected_qid:
            q = get_question_by_id(selected_qid)
            if q:
                qtext = f"""
【題目】
{q['題幹']}

【選項】
""" + "\n".join([f"({k}) {v}" for k, v in q['選項'].items()])
        student_ans, correct_ans = get_student_answer_and_truth(selected_qid) if selected_qid else (None, None)

        summary = StudentModel().export_summary()
        summary_text = json.dumps(summary, ensure_ascii=False, indent=2)

        # 組合 prompt
        parts = []
        if qtext:
            parts.append(qtext)
        if student_ans and correct_ans:
            parts.append(f"【學生作答】選了 {student_ans}，正確答案是 {correct_ans}")
        parts.append(f"【學生說明】\n{user_input}")
        parts.append(f"【學生近期摘要】\n{summary_text}")
        full_prompt = "\n\n".join(parts)

        # 選擇對應 agent
        if "診斷" in style:
            agent = diagnose_agent
        elif "補充" in style:
            agent = extend_agent
        else:
            agent = guide_agent

        st.session_state.chat_history.append(("你", user_input))
        with st.spinner("AI 教練回應中..."):
            result = asyncio.run(Runner.run(agent, input=full_prompt))
            st.session_state.chat_history.append(("AI 教練", result.final_output))

    for speaker, msg in st.session_state.chat_history:
        if speaker == "你":
            st.markdown(f"**🧑‍🎓 你：** {msg}")
        else:
            st.markdown(f"**🤖 AI 教練：** {msg}")
