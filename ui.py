import streamlit as st
from database import get_all_queries

def show_query_history():
    st.subheader("🕘 查詢紀錄")
    for user_input, response in get_all_queries():
        with st.expander(f"需求：{user_input[:30]}..."):
            st.markdown(f"**🔍 AI 回應：**\n{response}")
