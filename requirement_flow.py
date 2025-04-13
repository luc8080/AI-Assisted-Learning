# === 檔案路徑：requirement_flow.py

import streamlit as st
import asyncio
import re
import json
import os
from dotenv import load_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel

# === 初始化 Gemini 客戶端 ===
load_dotenv()
client = AsyncOpenAI(
    base_url=os.getenv("GOOGLE_GEMINI_ENDPOINT"),
    api_key=os.getenv("GOOGLE_GEMINI_API_KEY")
)
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

# === RequirementExtractor Agent 設定 ===
requirement_agent = Agent(
    name="RequirementExtractor",
    instructions="""
你是一位積層類磁性元件應用顧問，專門協助客戶釐清需求，並推薦最合適的 Tai-Tech 積層磁性元件產品。

使用者可能會輸入自然語言需求（如：600Ω、500mA、工業應用）或提供競品料號（如：MPZ1608S600AT）。

請根據情境萃取以下欄位（若有）：
- impedance（阻抗，Ω）
- dcr（直流電阻，Ω）
- current（額定電流，mA）
- size（封裝尺寸）
- application（應用場景）
- temp_min / temp_max（溫度）
- reference_part_number（競品料號）
- reference_vendor（競品品牌）

當你認為資訊足夠時，請只回傳「單一 JSON 物件」，不要回傳陣列。
""",
    model=model
)

# === 初始化 session 狀態 ===
def init_flow_state():
    if "requirement_messages" not in st.session_state:
        st.session_state.requirement_messages = [ {
            "role": "assistant",
            "content": "👋 歡迎，我是 Tai-Tech 磁性元件推薦助理。\n\n請輸入應用需求（如阻抗、電流等）或競品料號（如 MPZ1608S601），我將協助您推薦合適產品。"
        }]
    if "requirement_final_result" not in st.session_state:
        st.session_state.requirement_final_result = None

# === AI 回合處理 ===
async def run_agent_turn(user_input: str):
    st.session_state.requirement_messages.append({"role": "user", "content": user_input})
    prompt = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.requirement_messages])

    result = await Runner.run(requirement_agent, prompt)
    reply = result.final_output.strip()
    st.session_state.requirement_messages.append({"role": "assistant", "content": reply})

    match = re.search(r"\{.*?\}|\[.*?\]", reply, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, (dict, list)):
                st.session_state.requirement_final_result = parsed
        except Exception:
            st.error("❌ 無法解析 AI 回應的 JSON 格式：")
            st.code(reply)

# === 對話 UI ===
def render_flow_ui():
    init_flow_state()
    st.subheader("🧠 AI 需求釐清")

    for msg in st.session_state.requirement_messages:
        role = "👤 使用者" if msg["role"] == "user" else "🤖 AI"
        with st.chat_message(role):
            st.markdown(msg["content"])

    if st.session_state.requirement_final_result:
        st.success("✅ 需求釐清完成")
        st.json(st.session_state.requirement_final_result)

        if st.button("🔄 重新開始釐清需求"):
            st.session_state.requirement_messages = []
            st.session_state.requirement_final_result = None
            st.rerun()
        return True

    user_input = st.chat_input("請輸入需求或回覆 AI 問題...")
    if user_input:
        asyncio.run(run_agent_turn(user_input))
        st.rerun()

    return False

# === 取得最終需求 dict ===
def get_final_requirements() -> dict:
    result = st.session_state.get("requirement_final_result", {})
    if isinstance(result, list):
        merged = {}
        for r in result:
            if isinstance(r, dict):
                merged.update(r)
        return merged
    elif isinstance(result, dict):
        return result
    return {}
