# recommendation.py
import asyncio
import streamlit as st
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, handoff
from dotenv import load_dotenv
import os
from database import get_all_product_specs, save_query_to_db

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
    prompt = f"用戶需求：{user_input}\n\n產品規格庫：{product_specs}\n請推薦最合適的鐵氧體磁珠產品。"
    result = await Runner.run(main_agent, prompt)
    return result.final_output

def process_recommendation(user_input):
    with st.spinner("AI 代理正在分析並推薦產品..."):
        response = asyncio.run(get_agent_response(user_input))
        save_query_to_db(user_input, response)
        st.success("推薦結果：")
        st.write(response)
