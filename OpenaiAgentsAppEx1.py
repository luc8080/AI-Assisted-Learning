import streamlit as st
import asyncio
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from dotenv import load_dotenv
import os

load_dotenv()

client = AsyncOpenAI(
    base_url=os.getenv("GOOGLE_GEMINI_ENDPOINT"),
    api_key=os.getenv("GOOGLE_GEMINI_API_KEY")
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

# 設定 Streamlit 應用標題
st.title("💡 OpenAI Agents + Streamlit Demo")

# 建立 agent 代理
agent = Agent(
    name="Assistant",
    instructions="你是一個智慧型助手，請幫助回答問題。",
    model=model
)

# 使用者輸入
user_input = st.text_input("請輸入你的問題：")

async def get_agent_response(prompt):
    result = await Runner.run(agent, prompt)
    return result.final_output

if st.button("提交"):
    if user_input:
        with st.spinner("AI Agent 回應中..."):
            response = asyncio.run(get_agent_response(user_input))
            st.success("AI Agent 回應：")
            st.write(response)
    else:
        st.warning("請輸入問題！")
