# 檔案路徑：assistant_core/populate_explanations.py

import sqlite3
import json
import os
from dotenv import load_dotenv
from agents import Agent, AsyncOpenAI, OpenAIChatCompletionsModel, Runner

DB_PATH = "data_store/question_bank.sqlite"

# === 初始化 LLM/Agent（以 Gemini 為例，OpenAI 亦可依實際切換） ===
load_dotenv()
client = AsyncOpenAI(
    base_url=os.getenv("GOOGLE_GEMINI_ENDPOINT"),
    api_key=os.getenv("GOOGLE_GEMINI_API_KEY")
)
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)
explanation_agent = Agent(
    name="ExplanationAgent",
    instructions="""
你是一位資深國文科AI老師，負責為學測國文素養題產生詳細解析。請依以下格式生成答案：
1. 解釋題幹的語意與核心考點。
2. 分析正確答案為何正確，並引用選項與文本。
3. 分析常見錯誤選項的混淆原因。
4. 給學生一條類型題型的學習建議。
請使用條列式，回應風格簡明專業。
""",
    model=model
)

def populate_explanations():
    # 加 event loop 保險，解決 Streamlit 多執行緒下 "no current event loop" 問題
    import asyncio
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, content, options, answer FROM questions WHERE explanation IS NULL OR explanation = ''")
    rows = c.fetchall()
    updated, failed = 0, 0

    for qid, content, options_json, answer in rows:
        try:
            # 組合題目與選項
            try:
                options = json.loads(options_json) if options_json else {}
            except Exception:
                options = {}
            option_str = "\n".join([f"({k}) {v}" for k, v in options.items()])

            prompt = f"""
題目：{content}
選項：
{option_str}
正解：{answer}

請根據上述資訊產生詳細解析：
1. 解釋題幹重點
2. 為何正解正確（引用題幹與選項）
3. 常見錯誤選項混淆原因
4. 類型學習建議（條列式）
"""
            result = Runner.run_sync(explanation_agent, input=prompt)
            explanation = result.final_output.strip()

            if explanation:
                c.execute("UPDATE questions SET explanation = ? WHERE id = ?", (explanation, qid))
                updated += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            print(f"補齊解析失敗（題號 {qid}）：{e}")

    conn.commit()
    conn.close()
    return updated, failed
