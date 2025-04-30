import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
from models.student_model import StudentModel

from assistant_core.learning_summary_agent import summary_agent
from agents import Runner
import asyncio
import json

DB_PATH = "data_store/user_log.sqlite"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student', 'teacher', 'admin'))
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answer_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_id INTEGER,
            question_id TEXT,
            student_answer TEXT,
            correct_answer TEXT,
            is_correct INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

# 根據登入者撈紀錄
def get_all_logs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (st.session_state.username,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return pd.DataFrame()
    user_id = row[0]
    df = pd.read_sql_query("SELECT * FROM answer_log WHERE user_id = ? ORDER BY timestamp DESC", conn, params=(user_id,))
    conn.close()
    return df

def run_summary_view():
    st.header("學習歷程紀錄")
    init_db()
    df = get_all_logs()

    if df.empty:
        st.info("尚未有任何作答紀錄。")
        return

    df['is_correct'] = df['is_correct'].map({1: '正確', 0: '錯誤'})
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    st.subheader("作答紀錄")
    st.dataframe(df.rename(columns={
        'timestamp': '作答時間',
        'question_id': '題號',
        'student_answer': '學生選項',
        'correct_answer': '正確答案',
        'is_correct': '結果'
    }), use_container_width=True)

    st.subheader("每日正確率趨勢")
    df_chart = df.copy()
    df_chart['date'] = df_chart['timestamp'].dt.date
    trend = df_chart.groupby('date')['is_correct'].apply(lambda x: (x == '✔️ 正確').mean()).reset_index()
    trend.columns = ['日期', '正確率']
    fig = px.line(trend, x='日期', y='正確率', markers=True)
    fig.update_layout(yaxis_tickformat=".0%", height=400)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("作答結果分布")
    pie_data = df['is_correct'].value_counts().reset_index()
    pie_data.columns = ['結果', '數量']
    fig2 = px.pie(pie_data, values='數量', names='結果', hole=0.4)
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("個人學習摘要 + 主題診斷")
    model = StudentModel()
    summary = model.export_summary()
    st.json(summary)

    st.subheader("錯題主題分布圖")
    topic_stats = model.get_wrong_topic_distribution()
    if topic_stats:
        df_topic = pd.DataFrame(list(topic_stats.items()), columns=["主題", "錯題數"])
        fig3 = px.bar(df_topic, x="主題", y="錯題數", title="常見錯誤主題統計")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("目前無可統計的錯題主題資料")

    st.subheader("AI 總結建議")
    if st.button("產生 AI 回饋建議"):
        prompt = json.dumps({
            "學習摘要": summary,
            "主題錯誤分布": topic_stats
        }, ensure_ascii=False, indent=2)

        try:
            result = asyncio.run(Runner.run(summary_agent, input=prompt))
            st.success(result.final_output)
        except Exception as e:
            st.warning(f"[AI 回饋失敗] {e}")

    model.close()
