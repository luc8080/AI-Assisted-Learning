# 檔案路徑：assistant_core/coach_agent.py

import os
import asyncio
from dotenv import load_dotenv
from agents import Agent, AsyncOpenAI, OpenAIChatCompletionsModel, Runner

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

# === 教練型 Agent（支援多輪精準個別化互動） ===
coach_agent = Agent(
    name="InteractiveCoach",
    instructions="""
你是一位親切且善於引導學生深入思考的 AI 國文老師。
請務必根據「學生每一輪的輸入內容」個別化回應，不要只照標準流程回答。
互動規則如下：

- 請先簡單回應學生本輪的輸入內容（例如：「你說你看不出來，讓我再說明一次⋯⋯」）。
- 根據題目、選項、正解和學生答案，針對學生的困難拆解思路，給予個人化協助。
- 反問部分要根據學生理解狀態調整難度，若學生主動問練習建議，請直接給建議。
- 互動三輪後請用鼓勵性語言總結並結束。
回答分兩段：【回覆】、【反問】。
回覆時僅能使用繁體中文，不可出現非中文亂碼、其他語系或莫名的特殊符號，專有名詞也請以中文解釋。
""",
    model=model
)

def run_coach_dialogue(
    question_info: dict,
    chat_history: list,
    user_input: str,
    style: str = "引導式（預設）",
    student_ans: str = None,
    correct_ans: str = None,
    summary: str = ""
):
    """
    多輪 AI 教練對話邏輯，回傳教練完整回答。
    """
    # 整理題目上下文
    ctx = []
    if question_info:
        if question_info.get("閱讀素材"):
            ctx.append(f"【閱讀素材/題組說明】\n{question_info['閱讀素材']}")
        ctx.append(f"【題目】\n{question_info['題幹']}")
        opts = question_info.get("選項", {})
        if opts:
            ctx.append("【選項】\n" + "\n".join([f"({k}) {v}" for k, v in opts.items()]))
        ctx.append(f"【正確答案】{question_info.get('正解') or correct_ans or ''}")
        if student_ans:
            ctx.append(f"【學生上次作答】{student_ans}")

    # 合併歷程對話
    dialogue = ""
    for speaker, msg in chat_history:
        dialogue += f"{speaker}：{msg}\n"
    dialogue += f"學生（本輪輸入）：{user_input}\n"

    # 組成最終 prompt
    prompt = "\n".join(ctx) \
        + "\n\n【歷程對話】\n" + dialogue \
        + f"\n【學生近期摘要】\n{summary}\n【教練風格】{style}"

    # ==== Event loop 安全防呆（Streamlit thread 環境下務必加上）====
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    # 送至 LLM
    result = Runner.run_sync(coach_agent, input=prompt)
    return result.final_output.strip()
