import sqlite3
import os
import time
import asyncio
from dotenv import load_dotenv
from agents import Agent, OpenAIChatCompletionsModel, AsyncOpenAI, Runner

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

# === 建立段落標題 Agent ===
paragraph_agent = Agent(
    name="ParagraphTagger",
    instructions="""
你是一位國文教師，負責根據題幹與出處判斷該題所屬段落標題。
請回覆簡潔段落名稱，例如：「材論第一段」、「師說末段」，或「未知」。
請只回傳段落名稱字串。
""",
    model=model
)

# === 補齊段落欄位 ===
def populate_paragraphs(db_path="data_store/question_bank.sqlite"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, source, stem FROM questions WHERE paragraph IS NULL OR paragraph = ''")
    rows = cursor.fetchall()

    updated = 0
    failed = 0
    for qid, source, stem in rows:
        prompt = f"出處：{source}\n題幹：{stem}"
        try:
            result = asyncio.run(Runner.run(paragraph_agent, input=prompt))
            time.sleep(3)
            paragraph = result.final_output.strip()
            cursor.execute("UPDATE questions SET paragraph = ? WHERE id = ?", (paragraph, qid))
            updated += 1
        except Exception as e:
            print(f"❌ 題號 {qid} 補段落失敗：{e}")
            failed += 1

    conn.commit()
    conn.close()
    return updated, failed

# 測試入口
if __name__ == "__main__":
    u, f = populate_paragraphs()
    print(f"✅ 段落補齊完成 {u} 題，失敗 {f} 題")
