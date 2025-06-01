# 檔案路徑：assistant_core/populate_keywords.py

import sqlite3
import os
import json
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
keywords_agent = Agent(
    name="KeywordsAgent",
    instructions="""
你是一位台灣高中國文素養導向命題專家。
請根據下列【閱讀文本】、【題幹】與【選項】，挑選本題最能代表學測國文素養核心的3-5個「主題關鍵詞」，這些關鍵詞將用於弱點診斷與個人化推薦。

- 關鍵詞必須與學測常見考點、知識點或解題素養能力高度相關，例如：「間接描寫」、「語境推論」、「篇章結構」、「文化素養」、「修辭技巧」、「成語運用」、「主旨判斷」、「詩歌賞析」、「現代文閱讀」等。
- 請以逗號分隔，**不要解釋、不要加註格式，只要關鍵詞**。

請務必遵照格式，直接回傳關鍵詞。
""",
    model=model
)

def populate_keywords():
    import asyncio
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, group_id, content, options FROM questions WHERE keywords IS NULL OR keywords = ''")
    rows = cursor.fetchall()
    updated, failed = 0, 0

    for qid, group_id, content, options_json in rows:
        # 取得對應題組的閱讀文本
        reading_text = ""
        if group_id:
            cursor.execute("SELECT reading_text FROM question_groups WHERE id = ?", (group_id,))
            row = cursor.fetchone()
            if row and row[0]:
                reading_text = row[0]

        try:
            try:
                options = json.loads(options_json) if options_json else {}
            except Exception:
                options = {}
            option_str = "\n".join([f"({k}) {v}" for k, v in options.items()])

            prompt = f"""
【閱讀文本】：
{reading_text if reading_text else "（無）"}

【題幹】：
{content}

【選項】：
{option_str}

請根據上述內容，僅回傳3-5個國文素養關鍵詞（逗號分隔），勿說明。
"""

            result = Runner.run_sync(keywords_agent, input=prompt)
            # 只取第一行且去除標點、多餘符號
            keywords = result.final_output.strip().replace("，", ",").replace("。", "")
            keywords = keywords.split("\n")[0].split("：")[-1].strip()
            # 保證3-5個以逗號分隔的詞
            if keywords and 2 <= keywords.count(",") <= 4:
                cursor.execute("UPDATE questions SET keywords = ? WHERE id = ?", (keywords, qid))
                updated += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            print(f"補齊關鍵詞失敗（題號 {qid}）：{e}")
    conn.commit()
    conn.close()
    return updated, failed

if __name__ == "__main__":
    updated, failed = populate_keywords()
    print(f"完成補齊關鍵詞：成功 {updated} 題，失敗 {failed} 題")
