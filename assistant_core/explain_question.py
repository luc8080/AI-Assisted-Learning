import os
import json
import pandas as pd
from dotenv import load_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from helpers.json_to_sqlite import insert_questions_to_db
from pathlib import Path
import asyncio
from models.student_model import StudentModel

# === 初始化 Gemini 模型 ===
load_dotenv()
api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
endpoint = os.getenv("GOOGLE_GEMINI_ENDPOINT")

if not api_key or not endpoint:
    raise ValueError("❌ 請設定 GOOGLE_GEMINI_API_KEY 與 GOOGLE_GEMINI_ENDPOINT 環境變數")

client = AsyncOpenAI(
    base_url=endpoint,
    api_key=api_key
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

# ✅ 僅首次執行時初始化題庫
json_path = "data_store/114_國綜.json"
sqlite_path = "data_store/question_bank.sqlite"
if not Path(sqlite_path).exists() and Path(json_path).exists():
    try:
        insert_questions_to_db(json_path)
        print("✅ 已初始化題庫")
    except Exception as e:
        print(f"[題庫初始化失敗] {e}")
else:
    print("✅ 資料庫已存在，略過題庫初始化")

# === 題目解析 Agent 設定 ===
explain_question_agent = Agent(
    name="ExplainQuestionAgent",
    instructions="""
你是一位熟悉臺灣學測國文素養題型的 AI 教師。
使用者會提供題目、選項、正確答案與學生作答，以及學生近期作答摘要。
請依以下格式輸出：

1. 題目大意（白話翻譯）
2. 為何正確答案正確？請引用題幹內容與推理過程。
3. 為何學生選項錯誤？指出混淆點或誤解處。
4. 根據學生歷史表現，是否出現類似錯誤趨勢？請整合提供建議。
5. 提供針對此類題型的學習建議、語文知識點與答題提醒。
6. 若學生答錯，請主動反問一個問題，引導他重新思考。
7. 回答風格請具備國文老師口吻，清楚邏輯、引導反思、避免模糊用語。

請以條列方式清楚回答，不需加前後說明詞。
""",
    model=model
)

def explain_question(prompt: str) -> str:
    result = asyncio.run(Runner.run(explain_question_agent, input=prompt))
    return result.final_output
