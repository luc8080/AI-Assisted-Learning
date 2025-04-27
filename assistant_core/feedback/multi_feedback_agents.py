from agents import Agent, OpenAIChatCompletionsModel, AsyncOpenAI, Runner
import os
from dotenv import load_dotenv
import asyncio

# === 初始化 Gemini API client ===
load_dotenv()
client = AsyncOpenAI(
    base_url=os.getenv("GOOGLE_GEMINI_ENDPOINT"),
    api_key=os.getenv("GOOGLE_GEMINI_API_KEY")
)
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

# === 多 Agent 定義 ===
explainer_agent = Agent(
    name="ExplainerAgent",
    instructions="""
你是一位資深國文教師，請你針對題目與選項，解釋正解的原因，條理清楚、易於學生理解。
請依以下格式輸出：
1. 題目大意
2. 為何正解正確
3. 每個選項的解析與誤導點
""",
    model=model
)

misconception_agent = Agent(
    name="MisconceptionAgent",
    instructions="""
你是一位學生作答分析師，擅長從學生選錯的選項推測其理解錯誤的來源，並給出心理錯誤類型與導正建議。
請依以下格式輸出：
1. 學生選擇與正解的差異
2. 錯誤可能來自的語文或思考誤區
3. 如何引導學生修正認知
""",
    model=model
)

coach_agent = Agent(
    name="CoachAgent",
    instructions="""
你是一位 AI 國文學習教練，請根據本題特性，提供學生後續練習與補強建議，可延伸至課本內容、文化知識、閱讀方法等。
請依以下格式輸出：
1. 類似題型提醒
2. 推薦學習方法
3. 建議閱讀或補充資料
""",
    model=model
)

summarizer_agent = Agent(
    name="SummarizerAgent",
    instructions="""
你是一位教學顧問，請根據三位教師（解析者、錯誤分析者、教練）的建議，整理出學生應掌握的重點。
請依以下格式輸出：
1. 核心提醒：本題關鍵概念是什麼？
2. 建議行動：避免什麼誤區、應如何補強？
3. 下一步建議：可做什麼延伸學習？
語氣務必親切、具引導性，適合學生閱讀。
""",
    model=model
)

agents = {
    "🎓 教學解析": explainer_agent,
    "👀 錯誤分析": misconception_agent,
    "🧭 學習建議": coach_agent
}

summarizer = summarizer_agent

# ✅ 並行回饋 + 每區塊獨立 spinner 呈現
async def run_agent_discussion(prompt: str, streamlit_container):
    placeholders = {title: streamlit_container.empty() for title in agents}

    async def run_single(title, agent):
        with placeholders[title]:
            with streamlit_container.status(f"{title} 回應中..."):
                result = await Runner.run(agent, input=prompt)
                streamlit_container.markdown(f"### {title}")
                streamlit_container.code(result.final_output, language="markdown")
                return title, result.final_output

    tasks = [run_single(title, agent) for title, agent in agents.items()]
    results = await asyncio.gather(*tasks)

    summary_input = "\n\n".join([f"{title}：\n{text}" for title, text in results])
    summary_result = await Runner.run(summarizer, input=summary_input)

    streamlit_container.markdown("## 🧠 回饋總結")
    streamlit_container.code(summary_result.final_output, language="markdown")
