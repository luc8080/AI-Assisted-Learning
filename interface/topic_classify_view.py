# 檔案路徑：interface/topic_classify_view.py

import streamlit as st
import sqlite3
import json
import os
import time
from dotenv import load_dotenv
from agents import Agent, OpenAIChatCompletionsModel, AsyncOpenAI, Runner
import asyncio

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

# === 建立分類用 Agent ===
classifier = Agent(
    name="TopicClassifier",
    instructions="""
你是一位台灣高中國文素養導向命題專家，負責為學測國文題目標記最適合的主題類別。
請依照下列類別，根據【閱讀文本】、【題幹】與【選項】做出判斷，只能擇一：
- 閱讀理解
- 文意推論
- 修辭判斷
- 語用語境
- 語詞詞義
- 篇章結構
- 文學常識
- 其他

請**僅回傳分類名稱**，不要解釋或加任何其他內容。
""",
    model=model
)

def classify_and_update_questions(db_path="data_store/question_bank.sqlite"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # 取出題目 & 其對應 group_id
    cursor.execute("SELECT id, group_id, content, options FROM questions WHERE topic IS NULL OR topic = '' OR topic = '待分類'")
    rows = cursor.fetchall()

    classified = 0
    failed = 0

    # 確保 event loop 正常
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    for qid, group_id, content, options_json in rows:
        # 補上閱讀文本
        reading_text = ""
        if group_id:
            cursor.execute("SELECT reading_text FROM question_groups WHERE id = ?", (group_id,))
            row = cursor.fetchone()
            if row and row[0]:
                reading_text = row[0]

        try:
            options = json.loads(options_json) if options_json else {}
        except Exception:
            options = {}
        option_str = ""
        if isinstance(options, dict) and options:
            for k in sorted(options.keys()):
                option_str += f"({k}) {options[k]}\n"

        # 新版 prompt
        prompt = f"""
【閱讀文本】
{reading_text if reading_text else "（無）"}

【題幹】
{content}

【選項】
{option_str}

請從以下類別中選擇一個最適合本題的主題分類，僅回傳分類名稱：
閱讀理解、文意推論、修辭判斷、語用語境、語詞詞義、篇章結構、文學常識、其他。
"""

        try:
            result = None
            for attempt in range(2):  # 最多重試一次
                try:
                    out = Runner.run_sync(classifier, input=prompt)
                    topic = out.final_output.strip().replace("：", "").replace(":", "")
                    topic = topic.split()[0]
                    valid_topics = {"閱讀理解", "文意推論", "修辭判斷", "語用語境", "語詞詞義", "篇章結構", "文學常識", "其他"}
                    if topic in valid_topics:
                        cursor.execute("UPDATE questions SET topic = ? WHERE id = ?", (topic, qid))
                        classified += 1
                        break
                    time.sleep(4.0)
                except Exception as inner:
                    if attempt == 0:
                        time.sleep(6)
                        continue
                    else:
                        print(f"題號 {qid} 分類失敗：{inner}")
                        failed += 1
        except Exception as e:
            print(f"未預期錯誤（題號 {qid}）：{e}")
            failed += 1

    conn.commit()
    conn.close()
    return classified, failed

# === Streamlit UI ===
def run_topic_classify_view():
    st.header("題目主題分類工具（AI 協助）")

    conn = sqlite3.connect("data_store/question_bank.sqlite")
    cursor = conn.cursor()

    # 題目分類統計圖表
    try:
        import pandas as pd
        import plotly.express as px
        df = pd.read_sql_query("SELECT topic, COUNT(*) as count FROM questions GROUP BY topic", conn)
        fig = px.bar(df, x="topic", y="count", title="現有主題分布統計圖", labels={"topic": "主題", "count": "題數"})
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"無法繪製統計圖：{e}")

    cursor.execute("SELECT COUNT(*) FROM questions WHERE topic IS NULL OR topic = '' OR topic = '待分類'")
    count = cursor.fetchone()[0]
    st.info(f"目前資料庫中共有 {count} 題尚未分類或為 '待分類'")

    if st.button("啟動分類任務"):
        with st.spinner("AI 分類進行中，請稍候..."):
            classified, failed = classify_and_update_questions()
        st.success(f"已完成 {classified} 題分類，失敗 {failed} 題")

    conn.close()
