import asyncio
import streamlit as st
import re
import json
import pandas as pd
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, handoff
from dotenv import load_dotenv
import os
from database import get_all_product_specs, save_query_to_db, get_all_product_specs_raw
from visualization import plot_radar_chart, plot_match_score_bar_chart, plot_comparison_radar_chart
from requirement_flow import render_flow_ui, get_final_requirements

load_dotenv()
client = AsyncOpenAI(
    base_url=os.getenv("GOOGLE_GEMINI_ENDPOINT"),
    api_key=os.getenv("GOOGLE_GEMINI_API_KEY")
)
model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client)

product_spec_agent = Agent(
    name="ProductSpecAgent",
    instructions="負責分析產品規格，從資料庫中檢索資訊並匹配用戶需求。",
    model=model
)
user_needs_agent = Agent(
    name="UserNeedsAgent",
    instructions="負責理解使用者的需求，將其轉換為技術規格。",
    model=model
)
main_agent = Agent(
    name="MainAgent",
    instructions="協調其他代理以滿足使用者需求。",
    model=model,
    handoffs=[
        handoff(product_spec_agent, tool_name_override="analyze_product_spec"),
        handoff(user_needs_agent, tool_name_override="interpret_user_needs")
    ]
)

def extract_spec_from_text(part_number: str, pdf_text: str) -> str:
    lines = pdf_text.splitlines()
    for i, line in enumerate(lines):
        if part_number.lower() in line.lower():
            start = max(i - 5, 0)
            end = min(i + 10, len(lines))
            return "\n".join(lines[start:end])
    return ""

async def get_agent_response(user_input):
    specs = get_all_product_specs()
    prompt = (
        f"用戶需求：{user_input}\n\n"
        f"產品資料庫：\n{specs}\n"
        "請推薦 2~3 個最符合需求的產品，並以 JSON 陣列格式回傳。"
    )
    result = await Runner.run(main_agent, prompt)
    return result.final_output

def parse_response_to_products(response):
    try:
        match = re.search(r"\[.*\]", response, re.DOTALL)
        return json.loads(match.group(0)) if match else []
    except Exception as e:
        st.error(f"❌ 無法解析 JSON：{e}")
        return []

def process_recommendation(_):
    st.markdown("🧠 **Step 1：釐清您的產品需求**")
    if not render_flow_ui():
        return
    user_req = get_final_requirements()
    user_input_str = json.dumps(user_req, ensure_ascii=False)

    with st.spinner("🤖 推薦中..."):
        raw_response = asyncio.run(get_agent_response(user_input_str))
        save_query_to_db(user_input_str, raw_response)

        st.success("🎯 推薦結果")
        st.code(raw_response, language="json")
        products = parse_response_to_products(raw_response)
        if not products: return

        plot_radar_chart(products)
        plot_match_score_bar_chart(products, user_req)
        df = pd.DataFrame(products)
        st.dataframe(df)
        st.download_button("📥 下載 JSON", json.dumps(products, indent=2, ensure_ascii=False), "recommendation.json")
        st.download_button("📥 下載 CSV", df.to_csv(index=False), "recommendation.csv")

def compare_and_recommend(part_number):
    st.markdown(f"🔍 比對競品料號：**{part_number}**")
    specs_raw = get_all_product_specs_raw()
    competitor_spec = None
    for _, vendor, filename, content in specs_raw:
        if part_number.lower() in content.lower():
            competitor_spec = extract_spec_from_text(part_number, content)
            break

    if not competitor_spec:
        st.warning("❌ 無法在資料庫中找到該競品料號相關資訊。")
        return

    st.code(competitor_spec)

    with st.spinner("🤖 AI 分析競品並推薦自家產品..."):
        prompt = (
            f"以下是競品產品的部分規格資訊：\n{competitor_spec}\n\n"
            f"請根據此產品特性，推薦 1~2 個自家產品作為最佳替代品，"
            f"推薦標準為：與競品規格最相近或更優的產品。\n"
            f"請以 JSON 陣列格式輸出，包括 name, vendor, impedance, current, dcr, temp_min, temp_max"
        )
        result = asyncio.run(Runner.run(main_agent, prompt))
        response = result.final_output
        st.success("🎯 自家產品推薦：")
        st.code(response, language="json")

        products = parse_response_to_products(response)
        if not products: return

        plot_comparison_radar_chart(part_number, competitor_spec, products)
        df = pd.DataFrame(products)
        st.dataframe(df)
        st.download_button("📥 下載 JSON", json.dumps(products, indent=2, ensure_ascii=False), "compare_result.json")
        st.download_button("📥 下載 CSV", df.to_csv(index=False), "compare_result.csv")
