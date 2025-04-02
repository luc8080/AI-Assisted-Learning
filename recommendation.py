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
你是一位磁珠產品顧問。你將收到使用者需求與一批候選產品資料，請從中推薦最合適的 2~3 筆，並說明推薦理由。

請回傳以下格式（JSON 陣列）：
[
  {
    "part_number": "HFZ3216-601T",
    "vendor": "Tai-Tech",
    "reason": "符合 10A 電流需求，且 DCR 僅 0.02Ω，效率最佳",
    "specs": {
      "impedance": 600,
      "current": 10000,
      "dcr": 0.02,
      "temp_min": -40,
      "temp_max": 100,
      "size": "3216"
    }
  }
]
""",
    model=model
)

def filter_candidates(requirements: dict, products: list[dict]) -> list[dict]:
    def match(product):
        if "impedance" in requirements and product.get("impedance") is not None:
            tolerance = requirements.get("impedance_tolerance", 0.25)
            expected = requirements["impedance"]
            if abs(product["impedance"] - expected) > tolerance * expected:
                return False
        if "current" in requirements and product.get("current") is not None:
            if product["current"] < requirements["current"]:
                return False
        if "dcr" in requirements and product.get("dcr") is not None:
            if product["dcr"] > requirements["dcr"]:
                return False
        if "temp_min" in requirements and product.get("temp_min") is not None:
            if product["temp_min"] > requirements["temp_min"]:
                return False
        if "temp_max" in requirements and product.get("temp_max") is not None:
            if product["temp_max"] < requirements["temp_max"]:
                return False
        return True

    return [p for p in products if match(p)]

async def get_agent_response(requirements: dict, candidates: list[dict]) -> str:
    prompt = f"""
🧾 使用者需求：
{json.dumps(requirements, ensure_ascii=False)}

📦 候選產品清單：
{json.dumps(candidates[:20], ensure_ascii=False)}
"""
    result = await Runner.run(recommendation_agent, prompt)
    return result.final_output

def parse_response(text: str) -> list[dict]:
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

    all_products = get_all_structured_specs()
    candidates = filter_candidates(requirements, all_products)

    if not candidates:
        st.error("❌ 找不到符合需求的產品")
        return

    with st.spinner("AI 正在推薦產品中..."):
        response_text = asyncio.run(get_agent_response(requirements, candidates))
        save_query_to_db(json.dumps(requirements, ensure_ascii=False), response_text)

        st.success("✅ 推薦完成")
        st.code(response_text, language="json")

        results = parse_response(response_text)
        if results:
            specs_only = []
            for r in results:
                if "specs" in r:
                    item = r["specs"].copy()
                    item["part_number"] = r.get("part_number", "產品")
                    specs_only.append(item)

            st.markdown("📊 推薦產品圖表分析")
            plot_recommendation_radar(specs_only)
            plot_condition_match_bar(requirements, specs_only)

            df = pd.DataFrame(results)
            st.dataframe(df)
            st.download_button("📥 下載推薦結果 (CSV)", df.to_csv(index=False), "recommended.csv")
