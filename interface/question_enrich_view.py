import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from assistant_core.populate_paragraphs import populate_paragraphs
import asyncio
from assistant_core.populate_keywords import populate_keywords

# === 題庫增補工具 ===
def run_question_enrich_view():
    st.header("題庫增補工具（AI 輔助段落與關鍵詞）")

    conn = sqlite3.connect("data_store/question_bank.sqlite")
    cursor = conn.cursor()

    # 統計段落與關鍵詞欄位狀態
    cursor.execute("SELECT COUNT(*) FROM questions WHERE paragraph IS NULL OR paragraph = ''")
    pending_paragraph = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM questions WHERE keywords IS NULL OR keywords = ''")
    pending_keywords = cursor.fetchone()[0]

    st.info(f"目前尚有 {pending_paragraph} 題未補段落，{pending_keywords} 題未補關鍵詞")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("補齊段落欄位"):
            with st.spinner("段落補齊中..."):
                u, f = populate_paragraphs()
                st.success(f"段落補齊完成：{u} 題成功、{f} 題失敗")

    with col2:
        if st.button("補齊關鍵詞欄位"):
            with st.spinner("關鍵詞補齊中..."):
                u, f = populate_keywords()
                st.success(f"關鍵詞補齊完成：{u} 題成功、{f} 題失敗")

    # 顯示統計圖（關鍵詞出現頻率）
    st.markdown("---")
    st.subheader("🔍 關鍵詞分布統計圖（依頻率）")
    df = pd.read_sql_query("SELECT keywords FROM questions WHERE keywords IS NOT NULL AND keywords != ''", conn)
    conn.close()

    from collections import Counter
    all_keywords = []
    for row in df["keywords"]:
        all_keywords.extend([kw.strip() for kw in row.split(",") if kw.strip()])

    if all_keywords:
        top_keywords = Counter(all_keywords).most_common(20)
        kw_df = pd.DataFrame(top_keywords, columns=["關鍵詞", "出現次數"])
        fig = px.bar(kw_df, x="關鍵詞", y="出現次數", title="前 20 高頻關鍵詞")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("目前無有效關鍵詞資料可分析")
