from agents import Agent, Runner, OpenAIChatCompletionsModel, AsyncOpenAI
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

# === 定義 Agent ===
assessor_agent = Agent(
    name="AssessorAgent",
    instructions="""
你是一位國文素養診斷師，請根據學生作答情況判斷是否需要錯誤分析，或可以直接給出學習建議。
請輸出以下格式：
- 初步診斷：學生答對或答錯的簡要描述
- 處理建議：請以 JSON 格式提供下一步動作，例如：
  {"handoff_to": "MisconceptionAgent"} 或 {"handoff_to": "CoachAgent"}
""",
    model=model
)

misconception_agent = Agent(
    name="MisconceptionAgent",
    instructions="""
你是一位錯誤分析師，請針對學生的誤選進行心理層面與知識層面分析，並建議修正策略。
""",
    model=model
)

coach_agent = Agent(
    name="CoachAgent",
    instructions="""
你是一位國文學習教練，請提供此題類型的後續補強建議與資源推薦。
""",
    model=model
)

agent_lookup = {
    "MisconceptionAgent": misconception_agent,
    "CoachAgent": coach_agent
}

# === 主控流程 ===
async def run_handoff_workflow(prompt: str):
    assessor_result = await Runner.run(assessor_agent, input=prompt)
    assessor_text = assessor_result.final_output

    import re, json
    match = re.search(r"\{.*\}", assessor_text)
    next_agent = ""
    if match:
        try:
            handoff_data = json.loads(match.group(0))
            next_agent = handoff_data.get("handoff_to")
        except Exception:
            pass

    if next_agent and next_agent in agent_lookup:
        next_result = await Runner.run(agent_lookup[next_agent], input=prompt)
        return {
            "診斷結果": assessor_text,
            "後續處理 ({})".format(next_agent): next_result.final_output
        }
    else:
        return {"診斷結果": assessor_text, "備註": "無有效 handoff 指令或 Agent 名稱錯誤"}

# ✅ 建議放置於 assistant_core/strategies/handoff_workflow.py，做為流程導向型 Agent 分流控制模組
