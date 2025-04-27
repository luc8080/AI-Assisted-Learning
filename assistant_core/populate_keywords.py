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

# === 建立關鍵詞 Agent ===
keyword_agent = Agent(
    name="KeywordTagger",
    instructions="""
你是一位國文教師，負責為試題擷取出 2~4 個代表此題重點的詞語。

請根據題幹與選項提取最能代表該題考點的詞彙。
回覆格式為 JSON 陣列，例如：["修辭", "比喻", "士人"]。
""",
    model=model
)

# === 補齊關鍵詞欄位 ===
def populate_keywords(db_path="data_store/question_bank.sqlite"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, stem, option_a, option_b, option_c, option_d FROM questions WHERE keywords IS NULL OR keywords = ''")
    rows = cursor.fetchall()

    updated = 0
    failed = 0
    for qid, stem, a, b, c, d in rows:
        prompt = f"題幹：{stem}\n選項：\n(A) {a}\n(B) {b}\n(C) {c}\n(D) {d}"
        try:
            result = asyncio.run(Runner.run(keyword_agent, input=prompt))
            time.sleep(3)
            import json
            kws = json.loads(result.final_output.strip())
            keywords = ", ".join(kws)
            cursor.execute("UPDATE questions SET keywords = ? WHERE id = ?", (keywords, qid))
            updated += 1
        except Exception as e:
            print(f"❌ 題號 {qid} 補關鍵詞失敗：{e}")
            failed += 1

    conn.commit()
    conn.close()
    return updated, failed

# 測試入口
if __name__ == "__main__":
    u, f = populate_keywords()
    print(f"✅ 關鍵詞補齊完成 {u} 題，失敗 {f} 題")
