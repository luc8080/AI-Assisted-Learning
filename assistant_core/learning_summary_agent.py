import os
from dotenv import load_dotenv
from agents import Agent, AsyncOpenAI, OpenAIChatCompletionsModel

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

# === 建立 AI 總結教練 Agent ===
summary_agent = Agent(
    name="StudentSummaryAgent",
    instructions="""
你是一位教學輔導老師，請根據學生近期作答狀況與錯題主題分布，給出三點條列式學習建議，語氣正向鼓勵並具體指引。請勿回覆超過三點。
""",
    model=model
)
