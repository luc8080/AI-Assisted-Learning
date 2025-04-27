import os
from dotenv import load_dotenv
from agents import Agent, AsyncOpenAI, OpenAIChatCompletionsModel

load_dotenv()

client = AsyncOpenAI(
    base_url=os.getenv("GOOGLE_GEMINI_ENDPOINT"),
    api_key=os.getenv("GOOGLE_GEMINI_API_KEY")
)
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

# 🧭 引導式教練
guide_agent = Agent(
    name="CoachGuideAgent",
    instructions="""
你是一位善於引導學生思考的國文教師。
請根據學生的提問，幫助他釐清題意、判斷選項差異，鼓勵學生自主發現解題關鍵，語氣正向親切。
若有提供題幹與選項，也可納入討論輔助。
""",
    model=model
)

# 🔍 診斷式教練
diagnose_agent = Agent(
    name="CoachDiagnoseAgent",
    instructions="""
你是一位嚴謹的國文教師，擅長診斷學生作答迷思與錯因。
請根據學生提問與題目內容，分析他可能的理解偏誤、推論錯誤，並明確指出關鍵失誤點。
""",
    model=model
)

# 📚 補充式教練
extend_agent = Agent(
    name="CoachExtendAgent",
    instructions="""
你是一位喜歡補充知識的國文教師，擅長延伸題目背後的背景知識、字詞用法、語境意涵。
請根據題目內容，補充相關文化知識、文學典故、修辭與語意應用。語氣輕鬆有趣。
""",
    model=model
)
