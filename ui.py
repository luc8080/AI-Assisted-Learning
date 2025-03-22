# ui.py
import streamlit as st
from database import get_all_queries

def show_user_input_section():
    return st.text_area(
        "請輸入您的鐵氧體磁珠需求：", 
        "應用: 抑制大電流電源線上的噪聲。\n"
        "阻抗需求: 在 100MHz 時，阻抗需達到 30Ω ±25%。\n"
        "額定電流: 電源線上的最大直流電流為 10A，因此需要額定電流至少 11000mA 的磁珠。\n"
        "直流電阻: DCR 越低越好，以減少功率損耗。\n"
        "尺寸限制: 可以使用 3216 尺寸的磁珠。\n"
        "工作溫度: 設備工作溫度範圍為 -20℃ 到 +100℃。\n"
        "安規要求: 必須符合 RoHS 規範。"
    )

def show_query_history():
    st.sidebar.subheader("🔎 查詢紀錄")
    queries = get_all_queries()
    for user_input, response in queries:
        with st.sidebar.expander(f"需求: {user_input[:30]}..."):
            st.write(f"**AI 回應:** {response}")
