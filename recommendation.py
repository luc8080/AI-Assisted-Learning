import asyncio
import streamlit as st
import re
import json
import pandas as pd
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, handoff
from dotenv import load_dotenv
import os
from database import get_all_product_specs, save_query_to_db
from visualization import plot_radar_chart

load_dotenv()

client = AsyncOpenAI(
    base_url=os.getenv("GOOGLE_GEMINI_ENDPOINT"),
    api_key=os.getenv("GOOGLE_GEMINI_API_KEY")
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

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

async def get_agent_response(user_input):
    product_specs = get_all_product_specs()
    prompt = (
        f"用戶需求：{user_input}\n\n"
        f"以下是產品資料庫內容：\n{product_specs}\n"
        "請根據需求推薦 2~3 個最合適的鐵氧體磁珠產品，"
        "並用 JSON 格式回傳如下：\n"
        "[\n"
        "  {{\"name\": \"型號1\", \"impedance\": 30, \"current\": 11000, \"dcr\": 1.5, \"temp_min\": -40, \"temp_max\": 125}},\n"
        "  {{\"name\": \"型號2\", \"impedance\": 33, \"current\": 9000, \"dcr\": 2.1, \"temp_min\": -20, \"temp_max\": 100}}\n"
        "]"
    )
    result = await Runner.run(main_agent, prompt)
    return result.final_output

def parse_response_to_products(response):
    """從 AI 回應中擷取 JSON 格式產品清單"""
    try:
        match = re.search(r"\[.*\]", response, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
    except Exception as e:
        st.error(f"❌ 無法解析推薦結果為結構化資料：{e}")
    return []

def process_recommendation(user_input):
    with st.spinner("🤖 AI 代理正在分析並推薦產品..."):
        raw_response = asyncio.run(get_agent_response(user_input))
        save_query_to_db(user_input, raw_response)

        st.success("🎯 推薦結果：")
        st.markdown("🔍 **原始 AI 回應內容**")
        st.code(raw_response, language="json")

        products = parse_response_to_products(raw_response)
        if not products:
            return

        # 雷達圖視覺化
        st.markdown("📊 **推薦產品雷達圖**")
        plot_radar_chart(products)

        # 表格視圖
        st.markdown("📋 **推薦產品詳細規格表**")
        df = pd.DataFrame(products)
        st.dataframe(df)

        # 下載功能
        st.download_button(
            label="📥 下載 JSON",
            data=json.dumps(products, ensure_ascii=False, indent=2),
            file_name="recommendation.json",
            mime="application/json"
        )

        st.download_button(
            label="📥 下載 CSV",
            data=df.to_csv(index=False),
            file_name="recommendation.csv",
            mime="text/csv"
        )
