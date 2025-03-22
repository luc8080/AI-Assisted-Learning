import streamlit as st
import json
import re
import asyncio
from agents import Agent, Runner, OpenAIChatCompletionsModel, AsyncOpenAI
import os
from dotenv import load_dotenv

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
    instructions=(
        "你是一個互動式需求解析助手，從使用者自然語言中提取產品需求參數。\n"
        "若資料不足，請回覆簡單補問，當資訊充足時，輸出如下 JSON 結構：\n"
        "{ \"impedance\": 30, \"current\": 11000, \"dcr\": 2.0, \"temp_min\": -40, \"temp_max\": 100, \"size\": \"3216\", \"impedance_tolerance\": 0.25 }"
    ),
    model=model
)

def init_state():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "final_requirements" not in st.session_state:
        st.session_state.final_requirements = None

def reset_flow():
    st.session_state.chat_history = []
    st.session_state.final_requirements = None

async def run_agent_turn(user_input):
    convo = "\n".join([f"User: {msg['user']}\nAI: {msg['ai']}" for msg in st.session_state.chat_history])
    prompt = f"{convo}\nUser: {user_input}"
    result = await Runner.run(requirement_agent, prompt)
    reply = result.final_output
    st.session_state.chat_history.append({"user": user_input, "ai": reply})
    try:
        match = re.search(r"\{.*\}", reply, re.DOTALL)
        st.session_state.final_requirements = json.loads(match.group(0))
        return "done"
    except:
        return "continue"

def render_flow_ui():
    init_state()
    for msg in st.session_state.chat_history:
        st.chat_message("user").write(msg["user"])
        st.chat_message("ai").write(msg["ai"])
    if st.session_state.final_requirements:
        st.success("✅ 已取得完整需求。")
        st.code(json.dumps(st.session_state.final_requirements, indent=2, ensure_ascii=False))
        return True
    user_input = st.chat_input("請輸入產品需求或回答 AI 補問：")
    if user_input:
        asyncio.run(run_agent_turn(user_input))
        st.rerun()
    return False

def get_final_requirements():
    return st.session_state.final_requirements
