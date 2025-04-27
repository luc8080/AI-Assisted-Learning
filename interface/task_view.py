import streamlit as st
from assistant_core.explain_question import explain_question
from data_store.question_loader import get_random_question, get_question_by_id
from models.student_model import StudentModel
from assistant_core.feedback.multi_feedback_agents import run_agent_discussion
import sqlite3
from datetime import datetime
import json

DB_PATH = "data_store/user_log.sqlite"

# 儲存作答紀錄到 SQLite
def save_log(qid, student_ans, correct_ans):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answer_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_id INTEGER,
            question_id TEXT,
            student_answer TEXT,
            correct_answer TEXT,
            is_correct INTEGER
        )
    """)
    cursor.execute("SELECT id FROM users WHERE username = ?", (st.session_state.username,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return
    user_id = row[0]
    cursor.execute("""
        INSERT INTO answer_log (timestamp, user_id, question_id, student_answer, correct_answer, is_correct)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (datetime.now().isoformat(), user_id, qid, student_ans, correct_ans, int(student_ans == correct_ans)))
    conn.commit()
    conn.close()

# === 單題作答與解析任務畫面 ===
def run_task_view():
    st.header("📝 素養題作答任務")

    if "from_wrongbook" in st.session_state:
        qid = st.session_state.pop("from_wrongbook")
        st.session_state.current_question = get_question_by_id(qid)

    if "current_question" not in st.session_state:
        st.session_state.current_question = get_random_question()

    q = st.session_state.current_question

    st.markdown(f"**題號：** {q['題號']}")
    st.markdown(f"**題目：** {q['題幹']}")

    student_answer = st.radio("請選出你認為最適當的選項：", options=list(q['選項'].keys()),
                               format_func=lambda x: f"({x}) {q['選項'][x]}")

    if st.button("提交作答並獲得解析"):
        is_correct = student_answer == q['正解']
        save_log(q['題號'], student_answer, q['正解'])

        if is_correct:
            st.success(f"✔️ 答對了！")
        else:
            st.error(f"❌ 答錯了，正確答案是：{q['正解']}")

        model = StudentModel()
        summary = model.export_summary()
        model.close()

        prompt = f"""
【題目】
{q['題幹']}

【選項】
{chr(10).join([f"({k}) {v}" for k, v in q['選項'].items()])}

【正確答案】{q['正解']}
【學生答案】{student_answer}

【學生近期學習摘要】
{json.dumps(summary, ensure_ascii=False, indent=2)}
"""

        st.markdown("---")
        st.subheader("🤖 AI 教學多觀點回饋")
        st.markdown("(系統將自動整合三位 AI 教師建議，最後提供一段重點回饋)")
        st.markdown("---")

        st.session_state.prompt = prompt
        st.session_state.run_multi_feedback = True

    if st.session_state.get("run_multi_feedback"):
        st.session_state.run_multi_feedback = False
        st.markdown("<div id='multi-agent-discussion'></div>", unsafe_allow_html=True)
        import asyncio
        asyncio.run(run_agent_discussion(st.session_state.prompt, streamlit_container=st))

    if st.button("下一題"):
        st.session_state.current_question = get_random_question()
        st.rerun()
