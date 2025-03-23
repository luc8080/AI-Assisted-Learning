# recommendation.py
import streamlit as st
import asyncio
import json
import re
import pandas as pd
from dotenv import load_dotenv
import os

from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from database import get_all_product_specs, save_query_to_db
from visualization import plot_recommendation_radar, plot_condition_match_bar
from requirement_flow import render_flow_ui, get_final_requirements

# === LLM 設定 ===
load_dotenv()
client = AsyncOpenAI(
    base_url=os.getenv("GOOGLE_GEMINI_ENDPOINT"),
    api_key=os.getenv("GOOGLE_GEMINI_API_KEY")
)
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

# === 主要 Agent ===
recommendation_agent = Agent(
    name="ProductRecommender",
    instructions="""
你是一位鐵氧體磁珠產品推薦助手。
請根據使用者輸入的技術需求，從提供的產品資料中推薦 2~3 個最合適的產品，並以 JSON 格式回應。

請回傳如下格式：
[
  {
    "name": "HFZ3216-601T",
    "vendor": "Tai-Tech",
    "impedance": 600,
    "current": 2000,
    "dcr": 0.02,
    "temp_min": -40,
    "temp_max": 100
  },
  ...
]

禁止模擬產品，請只從提供的產品資料中挑選。
如無完全符合的，也請列出最接近的 1-2 個並說明理由。
""",
    model=model
)

async def get_agent_response(requirements: dict) -> str:
    product_text = get_all_product_specs()
    prompt = f"""
📌 使用者需求：
{json.dumps(requirements, ensure_ascii=False)}

📘 產品資料庫內容如下（文字格式）：
{product_text[:12000]}  # 限制最多前 12000 字以避免 token 爆炸

請根據需求從產品內容中推薦最合適的產品，並回傳 JSON 清單。
"""
    result = await Runner.run(recommendation_agent, prompt)
    return result.final_output

def parse_response_to_json(text: str) -> list[dict]:
    try:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        return json.loads(match.group(0)) if match else []
    except:
        return []

def process_recommendation(_):
    if not render_flow_ui():
        return

    requirements = get_final_requirements()
    if not requirements:
        st.warning("⚠️ 尚未完成需求釐清")
        return

    with st.spinner("AI 正在分析產品資料並推薦中..."):
        response_text = asyncio.run(get_agent_response(requirements))
        save_query_to_db(json.dumps(requirements, ensure_ascii=False), response_text)

        st.success("✅ 推薦完成")
        st.code(response_text, language="json")

        products = parse_response_to_json(response_text)
        if products:
            st.markdown("📊 推薦產品圖表分析")
            plot_recommendation_radar(products)
            plot_condition_match_bar(requirements, products)
            df = pd.DataFrame(products)
            st.dataframe(df)
            st.download_button("📥 下載推薦清單 (CSV)", df.to_csv(index=False), "recommended.csv")
