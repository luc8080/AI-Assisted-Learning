import os
from agents import Agent, AsyncOpenAI, OpenAIChatCompletionsModel, handoff
from database import get_all_product_specs
from dotenv import load_dotenv

# 加載環境變數
load_dotenv()

# 設定 API 客戶端
client = AsyncOpenAI(
    base_url=os.getenv("GOOGLE_GEMINI_ENDPOINT"),
    api_key=os.getenv("GOOGLE_GEMINI_API_KEY")
)

# 設定 OpenAI 代理模型
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

# 定義 AI 代理
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

# 主代理，協調其他代理完成產品推薦
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
    """執行 AI 代理並回應推薦結果"""
    product_specs = get_all_product_specs()
    
    if not product_specs:
        return "❌ 資料庫無產品規格，請先上傳 PDF。"

    prompt = f"用戶需求：{user_input}\n\n產品規格庫：{product_specs}\n請推薦最合適的鐵氧體磁珠產品。"
    result = await main_agent.run(prompt)
    
    return result.final_output
