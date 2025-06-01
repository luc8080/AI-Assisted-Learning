# 檔案路徑：assistant_core/populate_paragraphs.py

import sqlite3
import os
from dotenv import load_dotenv
from agents import Agent, AsyncOpenAI, OpenAIChatCompletionsModel, Runner

DB_PATH = "data_store/question_bank.sqlite"

# === 初始化 LLM/Agent ===
load_dotenv()
client = AsyncOpenAI(
    base_url=os.getenv("GOOGLE_GEMINI_ENDPOINT"),
    api_key=os.getenv("GOOGLE_GEMINI_API_KEY")
)
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)
paragraph_agent = Agent(
    name="ParagraphAgent",
    instructions="""
你是一位國文素養導向題命題老師，請根據題幹，產生一段100字以內、能作為該題閱讀背景素材的現代語境短文。
內容需自然且具有閱讀素養風格，不可抄題幹內容。
""",
    model=model
)

def populate_paragraphs():
    # Event loop 保險，防止 "no current event loop" 問題
    import asyncio
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 只取沒有 paragraph 或為空的題目
    cursor.execute("SELECT id, content FROM questions WHERE paragraph IS NULL OR paragraph = ''")
    rows = cursor.fetchall()
    updated, failed = 0, 0

    for qid, content in rows:
        prompt = f"請根據下列題目內容，補充一段適合作為素養閱讀素材的背景短文（100字內）：\n{content}"
        try:
            result = Runner.run_sync(paragraph_agent, input=prompt)
            paragraph = result.final_output.strip()
            if paragraph:
                cursor.execute("UPDATE questions SET paragraph = ? WHERE id = ?", (paragraph, qid))
                updated += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            print(f"補齊段落失敗（題號 {qid}）：{e}")

    conn.commit()
    conn.close()
    return updated, failed
