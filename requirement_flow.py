# requirement_flow.py
import streamlit as st
import asyncio
import re
import json
from dotenv import load_dotenv
import os
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel

load_dotenv()

client = AsyncOpenAI(
    base_url=os.getenv("GOOGLE_GEMINI_ENDPOINT"),
    api_key=os.getenv("GOOGLE_GEMINI_API_KEY")
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

requirement_agent = Agent(
    name="RequirementExtractor",
    instructions="""
你是一位磁珠應用顧問，負責釐清使用者的產品需求，並最終以 JSON 格式輸出關鍵參數。

使用者可能會輸入不完整的需求，你需要補問直到資訊完整。當收集到以下欄位後，請回傳 JSON 結構，不再追問：

- impedance
- impedance_tolerance（比例, 例如 0.25）
- dcr
- current
- temp_min
- temp_max
- size
- application

僅當條件齊全時才回傳 JSON 格式，否則繼續追問。
""",
    model=model
)

def init_flow_state():
    if "requirement_messages" not in st.session_state:
        st.session_state.requirement_messages = []
    if "requirement_final_result" not in st.session_state:
        st.session_state.requirement_final_result = None

async def run_agent_turn(user_input: str):
    st.session_state.requirement_messages.append({"role": "user", "content": user_input})

    # 將多輪對話訊息合併為 prompt 字串
    prompt = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.requirement_messages])

    result = await Runner.run(requirement_agent, prompt)
    reply = result.final_output

    st.session_state.requirement_messages.append({"role": "assistant", "content": reply})

    # 嘗試從 AI 回應中擷取 JSON 結構
    match = re.search(r"\{.*\}", reply, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            st.session_state.requirement_final_result = parsed
        except:
            pass

def render_flow_ui():
    init_flow_state()
    st.subheader("🧠 AI 需求釐清")

    # 顯示歷史對話
    for msg in st.session_state.requirement_messages:
        role = "👤 使用者" if msg["role"] == "user" else "🤖 AI"
        with st.chat_message(role):
            st.markdown(msg["content"])

    # 若已完成釐清
    if st.session_state.requirement_final_result:
        st.success("✅ 需求釐清完成")
        st.json(st.session_state.requirement_final_result)
        return True

    # 使用者輸入
    user_input = st.chat_input("請輸入需求或回覆 AI 問題...")
    if user_input:
        asyncio.run(run_agent_turn(user_input))
        st.rerun()

    return False

def get_final_requirements():
    return st.session_state.get("requirement_final_result", None)
