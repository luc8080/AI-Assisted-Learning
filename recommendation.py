# === 檔案路徑：recommendation.py
# === 功能說明：
# 提供基於使用者技術需求的磁性元件產品推薦流程，整合需求釐清、資料庫比對、AI 精選與視覺化展示。
# 支援競品料號、自家產品比對推薦、推薦理由展示、結果下載與產品比較。
# === 最後更新：2025-04-13

import streamlit as st
import asyncio
import os
import json
import re
import pandas as pd
from dotenv import load_dotenv

from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from database import get_all_structured_specs, save_query_to_db
from visualization import plot_condition_match_bar, plot_recommendation_radar
from requirement_flow import render_flow_ui, get_final_requirements
from rule_recommender import filter_with_rejection_reason, sort_candidates

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

# === 推薦用 Agent 設定 ===
recommendation_agent = Agent(
    name="ProductRecommender",
    instructions="""
你是一位磁性元件產品推薦助手，專門處理 Tai-Tech 自家積層磁性產品的應用建議。
你會收到兩筆資料：
1. 使用者輸入的技術需求（dict 格式，可能包含參考料號）
2. Tai-Tech 所有產品的候選清單（list[dict]）

請根據條件推薦最多 3 筆產品，每筆包含：
- part_number
- vendor
- impedance
- dcr
- current
- application
- source_filename
- reason（推薦理由）

❗請只回傳 JSON 陣列，不加任何說明或標註文字。
""",
    model=model
)

# === LLM 推薦邏輯 ===
async def get_ai_recommendation(requirements: dict, candidates: list[dict]) -> list[dict]:
    prompt = f"""以下是使用者需求條件：\n{requirements}\n\n請從下列產品中挑選最合適的推薦產品（最多 3 筆）：\n\n{candidates}"""
    result = await Runner.run(recommendation_agent, prompt)
    reply = result.final_output.strip()

    try:
        match = re.search(r"\[.*?\]", reply, re.DOTALL)
        parsed = json.loads(match.group(0)) if match else json.loads(reply)
        if isinstance(parsed, list):
            return [p for p in parsed if isinstance(p, dict) and "part_number" in p]
    except Exception as e:
        st.error(f"❌ LLM 回傳解析失敗：{e}")
        st.code(reply[:1000])
    return []

# === 摘要卡片展示 ===
def summarize_product_card(product: dict):
    def get_val(v): return "N/A" if v in [None, ""] else v
    st.markdown(f"""
    #### 📦 {get_val(product.get("part_number"))} ({get_val(product.get("vendor"))})
    - **阻抗**：{get_val(product.get("impedance"))} Ω
    - **DCR**：{get_val(product.get("dcr"))} Ω
    - **額定電流**：{get_val(product.get("current"))} mA
    - **應用場景**：{get_val(product.get("application"))}
    - **來源**：{get_val(product.get("source_filename"))}
    - **推薦理由**：{get_val(product.get("reason"))}
    """)

# === 主推薦流程 ===
def process_recommendation(user_input: str = None):
    st.info("🔍 請回答幾個問題來幫助我們了解您的需求")
    if not render_flow_ui():
        return

    requirements = get_final_requirements()
    if not isinstance(requirements, dict):
        st.warning("⚠️ 解析錯誤：需求格式應為 dict")
        return

    st.success("✅ 已完成需求釐清")
    st.json(requirements)

    all_specs = get_all_structured_specs()
    candidates = filter_with_rejection_reason(all_specs, requirements)
    sorted_candidates = sort_candidates(candidates, requirements)

    if not sorted_candidates:
        st.warning("❌ 找不到符合條件的產品")
        return

    st.info("🤖 AI 正在從候選產品中挑選最佳推薦...")
    top_k = asyncio.run(get_ai_recommendation(requirements, sorted_candidates[:30]))

    if not top_k:
        st.warning("⚠️ AI 未回傳推薦結果，將改用預設排序")
        top_k = sorted_candidates[:3]

    st.subheader("🎯 符合需求的推薦產品")
    plot_condition_match_bar(requirements, top_k)
    plot_recommendation_radar(top_k)

    for p in top_k:
        if isinstance(p, dict):
            summarize_product_card(p)

    st.markdown("### 📤 推薦結果下載")
    df_result = pd.DataFrame(top_k)
    export_columns = [
        "part_number", "vendor", "impedance", "dcr", "current",
        "application", "source_filename", "reason"
    ]
    df_result = df_result[[col for col in export_columns if col in df_result.columns]]

    col1, col2 = st.columns(2)
    with col1:
        st.download_button("📥 下載 CSV", df_result.to_csv(index=False), "recommendation.csv", "text/csv")
    with col2:
        st.download_button("📥 下載 JSON", df_result.to_json(orient="records", force_ascii=False), "recommendation.json", "application/json")

    st.markdown("### 📊 推薦產品比較表")
    if "part_number" in df_result.columns:
        st.dataframe(df_result.set_index("part_number"), use_container_width=True)
    else:
        st.dataframe(df_result, use_container_width=True)

    save_query_to_db(json.dumps(requirements, ensure_ascii=False), json.dumps(top_k, ensure_ascii=False))
