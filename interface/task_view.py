# 檔案路徑：interface/task_view.py

import streamlit as st
from data_store.question_loader import get_random_question, get_question_by_id
from models.student_model import StudentModel
from assistant_core.feedback.multi_feedback_agents import run_agent_discussion
import sqlite3
from datetime import datetime
import json

LOG_DB_PATH = "data_store/user_log.sqlite"

def save_log(qid, student_ans, correct_ans, group_id=None, sub_id=None):
    conn = sqlite3.connect(LOG_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (st.session_state.username,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return
    user_id = row[0]
    cursor.execute("""
        INSERT INTO answer_log (timestamp, user_id, question_id, student_answer, correct_answer, is_correct, group_id, sub_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (datetime.now().isoformat(), user_id, qid, student_ans, correct_ans, int(student_ans == correct_ans), group_id, sub_id))
    conn.commit()
    conn.close()

def run_task_view():
    st.header("素養題作答任務")

    # 題庫載入判斷
    if "from_wrongbook" in st.session_state:
        qid = st.session_state.pop("from_wrongbook")
        st.session_state.current_question = get_question_by_id(qid)
        st.session_state.current_group_progress = None

    if "current_question" not in st.session_state:
        st.session_state.current_question = get_random_question()
        st.session_state.current_group_progress = None

    q = st.session_state.get("current_question")
    if not q:
        st.warning("找不到可作答題目，請聯絡管理員補充題庫。")
        return

    # 單題模式
    if q.get("type") == "single":
        _show_single_question(q)
    # 題組模式
    elif q.get("type") == "group":
        if "current_group_progress" not in st.session_state or st.session_state.current_group_progress is None:
            st.session_state.current_group_progress = 0
        questions = q["questions"]
        total_subs = len(questions)
        idx = st.session_state.current_group_progress

        st.markdown(f"**[題組] {q.get('title','')}**")
        st.markdown(f"**主題/分類：** {q.get('category', '')}")
        st.info(f"閱讀文本：\n{q['reading_text']}")
        st.markdown(f"---\n**小題 {idx+1} / {total_subs}**")
        subq = questions[idx]
        _show_single_question(subq, group=q, group_sub_idx=idx)

        # 下一小題/結束題組
        if st.session_state.get("show_next_group_subq_btn"):
            if idx + 1 < total_subs:
                if st.button("下一小題"):
                    st.session_state.current_group_progress += 1
                    st.session_state.show_next_group_subq_btn = False
                    st.rerun()
            else:
                if st.button("完成本題組，進入新題目"):
                    st.session_state.current_question = get_random_question()
                    st.session_state.current_group_progress = None
                    st.session_state.show_next_group_subq_btn = False
                    st.rerun()
    # 題組小題（直接用id查）模式
    elif q.get("type") == "group_sub":
        group = {
            "title": q.get("group_title", ""),
            "category": q.get("category", ""),
            "reading_text": q.get("reading_text", "")
        }
        _show_single_question(q, group=group, group_sub_idx=None)
    else:
        st.error("題庫結構錯誤或不支援的題型。")

# ========== 單題顯示與作答（含題組子題） ==========
def _show_single_question(q, group=None, group_sub_idx=None):
    # 決定正確的題號 (單題用題號、題組小題用 sub_id)
    qid = q.get('題號') or q.get('sub_id')
    st.markdown(f"**題號：** {qid}")
    if group:
        st.markdown(f"**所屬題組：** {group.get('title','')}")
    st.markdown(f"**題目：** {q.get('題幹','（缺題幹）')}")
    options = q.get('選項')
    if not isinstance(options, dict) or not options:
        st.error("選項資料異常，請聯絡管理員檢查題庫。")
        return
    correct_ans = q.get('正解') or q.get('answer')
    student_answer = st.radio(
        "請選出你認為最適當的選項：",
        options=list(options.keys()),
        format_func=lambda x: f"({x}) {options[x]}"
    )

    # 只顯示正確/錯誤，不直接顯示AI解析
    if st.button("提交作答", key=f"submit_{qid}"):
        group_id = group.get('group_id') if group else None
        sub_id = q.get('sub_id') if 'sub_id' in q else None
        save_log(qid, student_answer, correct_ans, group_id, sub_id)

        is_correct = student_answer == correct_ans
        if is_correct:
            st.success("答對了！")
        else:
            st.error(f"答錯了，正確答案是：{correct_ans}")

        # === 展開解析按鈕（資料庫有才顯示） ===
        explanation = q.get("解析") or q.get("explanation")
        if explanation and explanation.strip():
            with st.expander("點此展開解析"):
                st.markdown(explanation)

        # 顯示下一題/下一小題按鈕
        st.session_state.show_next_group_subq_btn = True

    # 單題時才顯示「下一題」
    if not group:
        if st.button("下一題"):
            st.session_state.current_question = get_random_question()
            st.rerun()
