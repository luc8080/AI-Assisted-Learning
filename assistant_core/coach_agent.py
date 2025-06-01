import os
import re
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

LANGUAGE_INSTRUCTION = """
你是一位親切且善於引導學生深入思考的 AI 國文老師。
請全程僅用繁體中文回覆，不可出現任何非繁體中文（包含亂碼、外語詞、特殊符號），
即使引用古文或名詞也須以中文說明，不可直接出現外語、日文、俄文等語言。
回覆需分兩段：【回覆】、【反問】。
請依據學生每輪內容個別化回應，三輪互動後以鼓勵語總結。
"""

coach_agent = Agent(
    name="InteractiveCoach",
    instructions=LANGUAGE_INSTRUCTION,
    model=model
)

def build_prompt(
    question_info: dict,
    chat_history: list,
    user_input: str,
    style: str = "引導式（預設）",
    student_ans: str = None,
    correct_ans: str = None,
    summary: str = ""
) -> str:
    """組裝完整 prompt"""
    ctx = []
    if question_info:
        if question_info.get("閱讀素材"):
            ctx.append(f"【閱讀素材/題組說明】\n{question_info['閱讀素材']}")
        if question_info.get("題幹"):
            ctx.append(f"【題目】\n{question_info['題幹']}")
        opts = question_info.get("選項", {})
        if opts:
            ctx.append("【選項】\n" + "\n".join([f"({k}) {v}" for k, v in opts.items()]))
        ctx.append(f"【正確答案】{question_info.get('正解') or correct_ans or ''}")
        if student_ans:
            ctx.append(f"【學生上次作答】{student_ans}")

    dialogue = "".join([f"{speaker}：{msg}\n" for speaker, msg in chat_history])
    dialogue += f"學生（本輪輸入）：{user_input}\n"

    prompt = "\n".join(ctx)
    prompt += f"\n\n【歷程對話】\n{dialogue}"
    prompt += f"\n【學生近期摘要】\n{summary}\n【教練風格】{style}"
    return prompt

def is_traditional_chinese(text: str, min_ratio: float = 0.7) -> bool:
    """
    判斷是否為繁體中文主體，避免亂碼/外語。
    min_ratio: 主要為中日韓字符所占比例
    """
    cjk_chars = re.findall(r'[\u4e00-\u9fff]', text)
    return (len(cjk_chars) / (len(text) + 1e-5)) > min_ratio

def run_coach_dialogue(
    question_info: dict,
    chat_history: list,
    user_input: str,
    style: str = "引導式（預設）",
    student_ans: str = None,
    correct_ans: str = None,
    summary: str = ""
) -> str:
    """
    多輪 AI 教練對話邏輯，回傳教練完整回答。
    """
    prompt = build_prompt(
        question_info, chat_history, user_input, style, student_ans, correct_ans, summary
    )

    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    for _ in range(2):  # 最多重生一次
        result = Runner.run_sync(coach_agent, input=prompt)
        output = result.final_output.strip()
        if is_traditional_chinese(output):
            return output
        prompt += "\n\n【系統提醒】上輪回答出現非繁體中文內容，請重新以純繁體中文生成。"
    # 若重生仍有問題，加註警告
    return "[警告] 回覆中偵測到非繁體中文內容，請檢查 prompt 設定。\n" + output
