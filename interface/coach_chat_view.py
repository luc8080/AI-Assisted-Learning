# 檔案路徑：interface/coach_chat_view.py

import streamlit as st
import sqlite3
import json
import asyncio
from models.student_model import StudentModel
from assistant_core.coach_agent import run_coach_dialogue

# === 取得題目完整內容（含閱讀素材、選項）===
def get_question_info_by_id(qid):
    conn = sqlite3.connect("data_store/question_bank.sqlite")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT q.id, q.content, q.options, q.answer, q.paragraph, g.reading_text, g.title
        FROM questions q
        LEFT JOIN question_groups g ON q.group_id = g.id
        WHERE q.id = ?
    """, (qid,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    qid, content, options_json, answer, paragraph, reading_text, group_title = row
    try:
        options = json.loads(options_json) if options_json else {}
    except Exception:
        options = {}
    return {
        "題號": qid,
        "題幹": content,
        "選項": options,
        "正解": answer,
        "閱讀素材": reading_text or paragraph or "",
        "題組名稱": group_title or ""
    }

# === 取得最近錯題題號 ===
def get_recent_wrong_qids(limit=10, username=None):
    conn = sqlite3.connect("data_store/user_log.sqlite")
    cursor = conn.cursor()
    if username:
        cursor.execute("""
            SELECT DISTINCT question_id FROM answer_log
            JOIN users ON users.id = answer_log.user_id
            WHERE is_correct = 0 AND users.username = ?
            ORDER BY timestamp DESC LIMIT ?
        """, (username, limit))
    else:
        cursor.execute("""
            SELECT DISTINCT question_id FROM answer_log
            WHERE is_correct = 0
            ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [str(row[0]) for row in rows]

# === 取得該題的學生作答與正解 ===
def get_student_answer_and_truth(qid, username=None):
    conn = sqlite3.connect("data_store/user_log.sqlite")
    cursor = conn.cursor()
    if username:
        cursor.execute("""
            SELECT student_answer, correct_answer FROM answer_log
            JOIN users ON users.id = answer_log.user_id
            WHERE question_id = ? AND users.username = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (qid, username))
    else:
        cursor.execute("""
            SELECT student_answer, correct_answer FROM answer_log
            WHERE question_id = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (qid,))
    row = cursor.fetchone()
    conn.close()
    return row if row else (None, None)

# === 主 coach chat 互動介面 ===
def run_coach_chat_view():
    st.title("AI 教練互動 - 多輪精準個別化對話")

    # 狀態初始化
    if "coach_chat_history" not in st.session_state:
        st.session_state.coach_chat_history = []
        st.session_state.coach_chat_round = 0
        st.session_state.coach_last_qinfo = None
        st.session_state.coach_last_student_ans = None

    username = st.session_state.get("username", None)

    # 選題（可帶出最近錯題）
    recent_wrong_qids = get_recent_wrong_qids(username=username)
    options = [""] + recent_wrong_qids
    selected_qid = st.selectbox("（可選）從最近錯題選擇題號：", options=options)

    question_info = None
    student_ans, correct_ans = None, None

    if selected_qid:
        question_info = get_question_info_by_id(selected_qid)
        student_ans, correct_ans = get_student_answer_and_truth(selected_qid, username=username)
        st.session_state.coach_last_qinfo = question_info
        st.session_state.coach_last_student_ans = student_ans

        # 顯示題目內容
        with st.expander("題目內容（含閱讀素材）", expanded=True):
            if question_info.get("閱讀素材"):
                st.markdown(f"**閱讀素材/題組說明：**\n{question_info['閱讀素材']}")
            st.markdown(f"**題幹：** {question_info['題幹']}")
            options_dict = question_info.get("選項", {})
            for k, v in options_dict.items():
                st.markdown(f"({k}) {v}")
            if correct_ans:
                st.caption(f"本題正確答案：{correct_ans}")
            elif question_info.get("正解"):
                st.caption(f"本題正確答案：{question_info['正解']}")
            if student_ans:
                st.caption(f"你上次作答答案：{student_ans}")

    # 教練回應風格
    style = st.selectbox("教練回應風格：", ["引導式（預設）", "診斷式", "延伸補充"])

    # 多輪對話流程
    prompt = st.chat_input("請輸入你想問 AI 教練的內容、困難、疑問或心得…")
    if prompt:
        # 收集所有歷史訊息（可讓 AI 看到所有前文）
        chat_history = st.session_state.coach_chat_history
        chat_round = st.session_state.coach_chat_round + 1

        # 學生歷程摘要
        summary = StudentModel().export_summary()
        summary_text = json.dumps(summary, ensure_ascii=False, indent=2)

        # 組完整 prompt 並送給 coach_agent
        full_answer = run_coach_dialogue(
            question_info=question_info or st.session_state.coach_last_qinfo,
            chat_history=chat_history,
            user_input=prompt,
            style=style,
            student_ans=student_ans or st.session_state.coach_last_student_ans,
            correct_ans=correct_ans,
            summary=summary_text
        )

        st.session_state.coach_chat_history.append(("你", prompt))
        st.session_state.coach_chat_history.append(("AI 教練", full_answer))
        st.session_state.coach_chat_round = chat_round

    # 聊天氣泡顯示
    for speaker, msg in st.session_state.coach_chat_history:
        with st.chat_message("user" if speaker == "你" else "assistant"):
            st.markdown(msg)

    if st.session_state.coach_chat_round >= 3:
        st.success("已達三輪討論，自動結束此次互動，請重新開始新的提問！")
        if st.button("重新開始新的互動"):
            st.session_state.coach_chat_history = []
            st.session_state.coach_chat_round = 0
            st.session_state.coach_last_qinfo = None
            st.session_state.coach_last_student_ans = None

# 若直接執行
if __name__ == "__main__":
    run_coach_chat_view()
