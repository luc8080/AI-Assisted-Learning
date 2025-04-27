import streamlit as st
from interface.task_view import run_task_view
from interface.summary_view import run_summary_view
from interface.handoff_view import run_handoff_view
from interface.wrongbook_view import run_wrongbook_view
from interface.coach_chat_view import run_coach_chat_view
from interface.topic_classify_view import run_topic_classify_view
from interface.question_enrich_view import run_question_enrich_view
from interface.login_view import run_login_view

st.set_page_config(page_title="素養導向學習助理 AI", layout="wide")

# ✅ 檢查是否登入
if 'username' not in st.session_state or 'role' not in st.session_state:
    run_login_view()
else:
    role = st.session_state.role

    if role == 'student':
        menu = st.sidebar.radio("功能選擇", [
            "📝 出題與作答",
            "📊 學習歷程紀錄",
            "📘 我的錯題本",
            "🧑‍🏫 AI 教練互動模式",
            "🧪 AI 診斷分析 (Handoff 模式)"
        ])

    elif role == 'teacher':
        menu = st.sidebar.radio("功能選擇", [
            "📚 教師後台 (開發中)",
            "🧑‍🏫 AI 教練互動模式"
        ])

    elif role == 'admin':
        menu = st.sidebar.radio("功能選擇", [
            "📝 出題與作答",
            "📊 學習歷程紀錄",
            "📘 我的錯題本",
            "🧑‍🏫 AI 教練互動模式",
            "🧪 AI 診斷分析 (Handoff 模式)",
            "🧠 題目主題分類",
            "🧩 題庫增補工具"
        ])

    else:
        st.error("未知角色，請重新登入。")
        run_login_view()

    if menu == "📝 出題與作答":
        run_task_view()
    elif menu == "📊 學習歷程紀錄":
        run_summary_view()
    elif menu == "📘 我的錯題本":
        run_wrongbook_view()
    elif menu == "🧑‍🏫 AI 教練互動模式":
        run_coach_chat_view()
    elif menu == "🧪 AI 診斷分析 (Handoff 模式)":
        run_handoff_view()
    elif menu == "🧠 題目主題分類":
        run_topic_classify_view()
    elif menu == "🧩 題庫增補工具":
        run_question_enrich_view()
    elif menu == "📚 教師後台 (開發中)":
        st.info("教師後台功能開發中...")
