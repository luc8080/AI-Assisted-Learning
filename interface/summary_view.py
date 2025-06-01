# 檔案路徑：interface/summary_view.py

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from models.student_model import StudentModel
import json
import asyncio
from assistant_core.learning_summary_agent import summary_agent
from agents import Runner

LOG_DB_PATH = "data_store/user_log.sqlite"
QB_DB_PATH = "data_store/question_bank.sqlite"

# 取得完整合併紀錄（answer_log join questions join question_groups）
def get_joined_logs():
    conn_log = sqlite3.connect(LOG_DB_PATH)
    conn_qb = sqlite3.connect(QB_DB_PATH)
    cursor = conn_log.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (st.session_state.username,))
    row = cursor.fetchone()
    if not row:
        conn_log.close()
        conn_qb.close()
        return pd.DataFrame()
    user_id = row[0]
    log_df = pd.read_sql_query("SELECT * FROM answer_log WHERE user_id = ? ORDER BY timestamp DESC", conn_log, params=(user_id,))
    if log_df.empty:
        conn_log.close()
        conn_qb.close()
        return log_df
    # 讀 questions
    q_df = pd.read_sql_query("SELECT * FROM questions", conn_qb)
    # 讀 group
    g_df = pd.read_sql_query("SELECT id as group_id, title, reading_text, category FROM question_groups", conn_qb)
    conn_log.close()
    conn_qb.close()
    # 型別對齊（確保 question_id 為 int）
    log_df['question_id'] = log_df['question_id'].astype(str)
    q_df['id'] = q_df['id'].astype(str)
    merged = pd.merge(log_df, q_df, left_on='question_id', right_on='id', how='left', suffixes=('', '_q'))
    merged = pd.merge(merged, g_df, left_on='group_id', right_on='group_id', how='left', suffixes=('', '_g'))
    return merged

def run_summary_view():
    st.header("學習歷程紀錄")

    df = get_joined_logs()
    if df.empty:
        st.info("尚未有任何作答紀錄。")
        return

    # 顯示用欄位與 rename
    df['is_correct'] = df['is_correct'].map({1: '正確', 0: '錯誤'})
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    display_cols = {
        'timestamp': '作答時間',
        'question_id': '題號',
        'content': '題目',
        'student_answer': '學生選項',
        'correct_answer': '正確答案',
        'is_correct': '結果',
        'topic': '主題',
        'keywords': '關鍵詞',
        'difficulty': '難度',
        'question_type': '題型',
        'title': '題組標題',
        'category': '分類'
    }
    disp_df = df[[col for col in display_cols if col in df.columns]].rename(columns=display_cols)

    st.subheader("作答紀錄")
    st.dataframe(disp_df, use_container_width=True)

    # 每日正確率趨勢
    st.subheader("每日正確率趨勢")
    df_chart = df.copy()
    df_chart['date'] = df_chart['timestamp'].dt.date
    trend = df_chart.groupby('date')['is_correct'].apply(lambda x: (x == '正確').mean()).reset_index()
    trend.columns = ['日期', '正確率']
    fig = px.line(trend, x='日期', y='正確率', markers=True)
    fig.update_layout(yaxis_tickformat=".0%", height=400)
    st.plotly_chart(fig, use_container_width=True)

    # 作答結果分布
    st.subheader("作答結果分布")
    pie_data = df['is_correct'].value_counts().reset_index()
    pie_data.columns = ['結果', '數量']
    fig2 = px.pie(pie_data, values='數量', names='結果', hole=0.4)
    st.plotly_chart(fig2, use_container_width=True)

    # 主題/關鍵詞/難度弱點分布
    st.subheader("主題/關鍵詞/難度弱點分析（僅統計錯題）")
    for col, label in [('topic', '主題'), ('keywords', '關鍵詞'), ('difficulty', '難度')]:
        err_df = df[df['is_correct'] == '錯誤']
        if not err_df.empty and col in err_df.columns:
            if col == 'keywords':
                from collections import Counter
                all_keywords = []
                for kws in err_df['keywords'].dropna():
                    all_keywords.extend([k.strip() for k in str(kws).split(",") if k.strip()])
                stats = Counter(all_keywords)
                chart_df = pd.DataFrame(stats.items(), columns=[label, '錯題數']).sort_values('錯題數', ascending=False)
            else:
                stats = err_df[col].value_counts()
                chart_df = pd.DataFrame({label: stats.index, '錯題數': stats.values})
            if not chart_df.empty:
                fig_kw = px.bar(chart_df, x=label, y='錯題數', title=f"錯題{label}分布")
                st.plotly_chart(fig_kw, use_container_width=True)

    # 顯示個人學習摘要
    st.subheader("個人學習摘要")
    model = StudentModel()
    summary = model.export_summary()
    st.json(summary)

    # AI 總結建議
    st.subheader("AI 總結建議")
    if st.button("產生 AI 回饋建議"):
        # timestamp 轉字串
        disp_df_json = disp_df.copy()
        if '作答時間' in disp_df_json.columns:
            disp_df_json['作答時間'] = disp_df_json['作答時間'].astype(str)
        prompt = json.dumps({
            "學習摘要": summary,
            "近30筆作答資料": disp_df_json.head(30).to_dict(orient="records")
        }, ensure_ascii=False, indent=2)
        try:
            result = asyncio.run(Runner.run(summary_agent, input=prompt))
            st.success(result.final_output)
        except Exception as e:
            st.warning(f"[AI 回饋失敗] {e}")

    model.close()

# 若直接執行
if __name__ == "__main__":
    run_summary_view()
