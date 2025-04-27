import streamlit as st
from assistant_core.strategies.handoff_workflow import run_handoff_workflow
import asyncio

def run_handoff_view():
    st.title("🧠 AI 學習診斷與回饋分流")

    sample_prompt = """
學生選擇：C
正確答案：B
題幹：下列哪一個最能表現文中主角的心理轉變？
選項：
(A) ...
(B) ...
(C) ...
(D) ...
"""

    prompt = st.text_area("請輸入學生作答情境與題目內容：", value=sample_prompt, height=200)

    if st.button("執行 AI 分析與分流回饋"):
        with st.spinner("AI 診斷中..."):
            result = asyncio.run(run_handoff_workflow(prompt))
        st.success("完成分析")
        for title, content in result.items():
            st.subheader(title)
            st.code(content, language="markdown")
