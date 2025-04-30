import streamlit as st
import sqlite3
import json
import os
import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from models.student_model import StudentModel

# === 初始化 Gemini 模型 ===
load_dotenv()
client = AsyncOpenAI(
    base_url=os.getenv("GOOGLE_GEMINI_ENDPOINT"),
    api_key=os.getenv("GOOGLE_GEMINI_API_KEY")
)
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

# === 教練型 Agent（優化版，多輪版） ===
coach_agent = Agent(
    name="InteractiveCoach",
    instructions="""
你是一位親切且善於引導學生深入思考的 AI 國文老師。
請務必根據提供的題目內容、選項、正確答案與學生作答資訊，進行精確且具依據的回覆。
回覆時請遵守以下規則：
- 必須引用題目或選項的原文字句作為依據，禁止編造未提供的內容。
- 必須清楚說明為何正確答案正確，以及學生的誤選可能原因。
- 回覆格式必須分為兩段：【回覆】與【反問】。
- 每輪討論請結尾提出一個簡單問題，引導學生再思考。
- 當達到第 3 輪時，請自動收斂並給予完整鼓勵性建議，結束互動。
""",
    model=model
)

# === 從資料庫取得題目內容 ===
def get_question_text_by_id(qid):
    conn = sqlite3.connect("data_store/question_bank.sqlite")
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
        "選項": {"A": row[3], "B": row[4], "C": row[5], "D": row[6]},
        "正解": row[7]
    }

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
        WHERE question_id = ?
        ORDER BY timestamp DESC LIMIT 1
    """, (qid,))
    row = cursor.fetchone()
    conn.close()
    return row if row else (None, None)

# === Coach Chat UI ===
def run_coach_chat_view():
    st.title("AI 教練互動 - 多輪版 (Chat UI)")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_round = 0

    style = st.selectbox("教練回應風格：", ["引導式（預設）", "診斷式", "延伸補充"])

    recent_wrong_qids = get_recent_wrong_qids()
    options = [""] + recent_wrong_qids
    selected_qid = st.selectbox("（可選）從最近錯題選擇題號：", options=options)

    question_info = None
    if selected_qid:
        question_info = get_question_text_by_id(selected_qid)
        if question_info:
            with st.expander("題目內容（供參考）"):
                st.markdown(f"**題目**：{question_info['題幹']}")
                for k, v in question_info['選項'].items():
                    st.markdown(f"({k}) {v}")
                show_answer = st.checkbox("顯示正確答案", value=False)
                if show_answer:
                    st.caption(f"本題正確答案：{question_info['正解']}")

    if prompt := st.chat_input("請輸入想問AI教練的內容..."):
        summary = StudentModel().export_summary()
        summary_text = json.dumps(summary, ensure_ascii=False, indent=2)

        prompt_parts = []
        if question_info:
            prompt_parts.append(f"【題目】\n{question_info['題幹']}\n\n【選項】\n(A) {question_info['選項']['A']}\n(B) {question_info['選項']['B']}\n(C) {question_info['選項']['C']}\n(D) {question_info['選項']['D']}\n【正確答案】{question_info['正解']}")
        prompt_parts.append(f"【學生說明】\n{prompt}")
        prompt_parts.append(f"【學生近期摘要】\n{summary_text}")
        prompt_parts.append(f"【教練風格】{style}")

        full_prompt = "\n\n".join(prompt_parts)

        st.session_state.chat_history.append(("你", prompt))

        with st.spinner("AI 教練思考中..."):
            result = asyncio.run(Runner.run(coach_agent, input=full_prompt))
            response = result.final_output.strip()
            st.session_state.chat_history.append(("AI 教練", response))

        st.session_state.chat_round += 1

    # 顯示聊天氣泡
    for speaker, msg in st.session_state.chat_history:
        with st.chat_message("user" if speaker == "你" else "assistant"):
            st.markdown(msg)

    if st.session_state.chat_round >= 3:
        st.success("已達三輪討論，自動結束此次互動，請重新開始新的提問！")
        if st.button("重新開始新的互動"):
            st.session_state.chat_history = []
            st.session_state.chat_round = 0
