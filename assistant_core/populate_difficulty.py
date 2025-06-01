# 檔案路徑：assistant_core/populate_difficulty.py

import sqlite3
import json
import os
from dotenv import load_dotenv
from agents import Agent, AsyncOpenAI, OpenAIChatCompletionsModel, Runner

DB_PATH = "data_store/question_bank.sqlite"

# === 初始化 LLM/Agent（以 Gemini 為例） ===
load_dotenv()
client = AsyncOpenAI(
    base_url=os.getenv("GOOGLE_GEMINI_ENDPOINT"),
    api_key=os.getenv("GOOGLE_GEMINI_API_KEY")
)
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)
difficulty_agent = Agent(
    name="DifficultyAgent",
    instructions="""
你是一位熟悉學測國文命題的資深教師，請判斷給定題目的難易度（1=簡單、2=中等、3=困難），僅回覆一個數字，不需解釋。
參考因素：選項混淆度、文本理解難度、推論層次、常見錯誤機率等。
""",
    model=model
)

def populate_difficulty():
    # Event loop 保險，防止 "no current event loop" 問題
    import asyncio
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, content, options FROM questions WHERE difficulty IS NULL OR difficulty = ''")
    rows = c.fetchall()
    updated, failed = 0, 0

    for qid, content, options_json in rows:
        try:
            try:
                options = json.loads(options_json) if options_json else {}
            except Exception:
                options = {}
            option_str = "\n".join([f"({k}) {v}" for k, v in options.items()])

            prompt = f"""
題目：{content}
選項：
{option_str}
請根據學測國文命題原則，判斷本題難易度（1=簡單，2=中等，3=困難）。
僅回覆一個阿拉伯數字。
"""
            result = Runner.run_sync(difficulty_agent, input=prompt)
            diff = result.final_output.strip()
            # 只取第一個數字，防呆
            diff_digit = [c for c in diff if c in "123"]
            if diff_digit:
                c.execute("UPDATE questions SET difficulty = ? WHERE id = ?", (diff_digit[0], qid))
                updated += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            print(f"補齊難度失敗（題號 {qid}）：{e}")

    conn.commit()
    conn.close()
    return updated, failed
