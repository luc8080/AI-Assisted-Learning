import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# 匯入你的 AI 補齊函式
from assistant_core.populate_paragraphs import populate_paragraphs
from assistant_core.populate_keywords import populate_keywords
from assistant_core.populate_explanations import populate_explanations
from assistant_core.populate_difficulty import populate_difficulty

# === 題庫增補工具 ===
def run_question_enrich_view():
    st.header("題庫增補工具（AI 輔助段落、關鍵詞、解析、難度）")

    conn = sqlite3.connect("data_store/question_bank.sqlite")
    cursor = conn.cursor()

    # 統計各欄位缺漏狀態
    cursor.execute("SELECT COUNT(*) FROM questions WHERE paragraph IS NULL OR paragraph = ''")
    pending_paragraph = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM questions WHERE keywords IS NULL OR keywords = ''")
    pending_keywords = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM questions WHERE explanation IS NULL OR explanation = ''")
    pending_explanation = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM questions WHERE difficulty IS NULL OR difficulty = ''")
    pending_difficulty = cursor.fetchone()[0]

    st.info(
        f"尚有 {pending_paragraph} 題未補段落、"
        f"{pending_keywords} 題未補關鍵詞、"
        f"{pending_explanation} 題未補解析、"
        f"{pending_difficulty} 題未補難度"
    )

    # 四個AI補齊按鈕
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("AI 補齊段落"):
            with st.spinner("段落補齊中..."):
                u, f = populate_paragraphs()
                st.success(f"段落補齊完成：{u} 題成功、{f} 題失敗")
    with col2:
        if st.button("AI 補齊關鍵詞"):
            with st.spinner("關鍵詞補齊中..."):
                u, f = populate_keywords()
                st.success(f"關鍵詞補齊完成：{u} 題成功、{f} 題失敗")
    with col3:
        if st.button("AI 補齊解析"):
            with st.spinner("解析補齊中..."):
                u, f = populate_explanations()
                st.success(f"解析補齊完成：{u} 題成功、{f} 題失敗")
    with col4:
        if st.button("AI 補齊難度"):
            with st.spinner("難度補齊中..."):
                u, f = populate_difficulty()
                st.success(f"難度補齊完成：{u} 題成功、{f} 題失敗")

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
