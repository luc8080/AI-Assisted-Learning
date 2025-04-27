import streamlit as st
import sqlite3
import json
import os
import time
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

# === 建立分類用 Agent ===
classifier = Agent(
    name="TopicClassifier",
    instructions="""
你是一位資深國文教師，負責為學測國文素養題標記主題類別。
請依照以下分類準則，從題幹與選項中判斷最適合的主題：
- 閱讀理解
- 文意推論
- 修辭判斷
- 語用語境
- 語詞詞義
- 篇章結構
- 文學常識
- 其他

請僅回傳分類名稱，不需解釋。
""",
    model=model
)

# === 執行分類任務 ===
def classify_and_update_questions(db_path="data_store/question_bank.sqlite"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, stem, option_a, option_b, option_c, option_d FROM questions WHERE topic IS NULL OR topic = '' OR topic = '待分類'")
    rows = cursor.fetchall()

    classified = 0
    failed = 0

    for qid, passage, a, b, c, d in rows:
        prompt = f"""
請根據下列題目內容判斷其主題分類：

題幹：{passage}
選項：
(A) {a}
(B) {b}
(C) {c}
(D) {d}

請從以下類別中選擇最適合的主題：閱讀理解、文意推論、修辭判斷、語用語境、語詞詞義、篇章結構、文學常識、其他。請僅回傳分類名稱。
"""
        try:
            result = None
            for attempt in range(2):  # 最多重試一次
                try:
                    result = Runner.run_sync(classifier, input=prompt)
                    time.sleep(4.0)
                    topic = result.final_output.strip()
                    if topic:
                        cursor.execute("UPDATE questions SET topic = ? WHERE id = ?", (topic, qid))
                        classified += 1
                        break
                except Exception as inner:
                    if attempt == 0:
                        time.sleep(6)
                        continue
                    else:
                        print(f"❌ 題號 {qid} 分類失敗：{inner}")
                        failed += 1
        except Exception as e:
            print(f"⚠️ 未預期錯誤（題號 {qid}）：{e}")
            failed += 1

    conn.commit()
    conn.close()
    return classified, failed

# === Streamlit UI ===
def run_topic_classify_view():
    st.header("🧠 題目主題分類工具（AI 協助）")

    conn = sqlite3.connect("data_store/question_bank.sqlite")
    cursor = conn.cursor()

    # 題目分類統計圖表
    try:
        import pandas as pd
        import plotly.express as px
        df = pd.read_sql_query("SELECT topic, COUNT(*) as count FROM questions GROUP BY topic", conn)
        fig = px.bar(df, x="topic", y="count", title="📊 現有主題分布統計圖", labels={"topic": "主題", "count": "題數"})
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"無法繪製統計圖：{e}")

    cursor.execute("SELECT COUNT(*) FROM questions WHERE topic IS NULL OR topic = '' OR topic = '待分類'")
    count = cursor.fetchone()[0]
    st.info(f"目前資料庫中共有 {count} 題尚未分類或為 '待分類'")

    if st.button("🚀 啟動分類任務"):
        with st.spinner("AI 分類進行中，請稍候..."):
            classified, failed = classify_and_update_questions()
        st.success(f"✅ 已完成 {classified} 題分類，失敗 {failed} 題")

    conn.close()
