import streamlit as st
import asyncio
import json
import re
import pandas as pd
from dotenv import load_dotenv
import os

from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from database import get_all_structured_specs, save_query_to_db
from visualization import plot_recommendation_radar, plot_condition_match_bar
from requirement_flow import render_flow_ui, get_final_requirements
from rule_recommender import filter_with_rejection_reason, sort_candidates

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

recommendation_agent = Agent(
    name="ProductRecommender",
    instructions="""
你是一位磁性元件產品推薦助手。
請根據使用者輸入的技術需求，從提供的產品資料中推薦 2~3 個最合適的產品，並以 JSON 格式回應。

格式範例如下：
[
  {
    "part_number": "HFZ3216-601T",
    "vendor": "Tai-Tech",
    "impedance": 600,
    "current": 2000,
    "dcr": 0.02,
    "temp_min": -40,
    "temp_max": 100,
    "reason": "符合阻抗需求，DCR 低，電流足夠"
  }
]
禁止模擬產品，只從提供產品中選擇。如無完全符合者，請挑最接近並說明理由。
""",
    model=model
)

async def get_agent_response(requirements: dict, products: list[dict]) -> str:
    product_text = json.dumps(products[:50], ensure_ascii=False)
    prompt = f"""
📌 使用者需求：
{json.dumps(requirements, ensure_ascii=False)}

📘 產品資料庫（結構化）如下：
{product_text}

請從中推薦最合適產品，以 JSON 陣列格式輸出（含推薦理由）。
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

    mode = st.radio("推薦模式", ["🧠 LLM 智慧推薦", "⚙️ 規則篩選"], horizontal=True)
    all_products = get_all_structured_specs()

    with st.spinner("🔍 正在進行推薦分析..."):
        if mode == "🧠 LLM 智慧推薦":
            response_text = asyncio.run(get_agent_response(requirements, all_products))
            save_query_to_db(json.dumps(requirements, ensure_ascii=False), response_text)
            products = parse_response_to_json(response_text)
            rejected = []
        else:
            matched, rejected = filter_with_rejection_reason(requirements, all_products)
            products = sort_candidates(matched, priority="current")[:3]
            response_text = json.dumps(products, ensure_ascii=False)

        if not products:
            st.warning("⚠️ 沒有找到符合條件的產品")
            return

        st.success("✅ 推薦完成")
        st.code(response_text, language="json")

        st.markdown("📊 推薦產品圖表分析")
        plot_recommendation_radar(products)
        plot_condition_match_bar(requirements, products)

        df = pd.DataFrame(products)
        st.dataframe(df)
        st.download_button("📥 下載推薦清單 (CSV)", df.to_csv(index=False), "recommended.csv")

        if mode == "⚙️ 規則篩選":
            with st.expander("🛑 被排除的產品（含排除理由）"):
                if rejected:
                    rejected_df = pd.DataFrame(rejected)
                    st.dataframe(rejected_df[["part_number", "rejected_reason"]])
                else:
                    st.info("所有產品皆符合條件，無排除項")
