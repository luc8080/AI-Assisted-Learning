import streamlit as st
import asyncio
from database import init_db, save_pdf_text_to_db, get_all_product_specs
from pdf_processor import extract_text_from_pdf
from ai_agents import get_agent_response

# 初始化資料庫
init_db()

# 設定 Streamlit 介面
st.sidebar.title("📂 產品規格書管理")
st.title("🔍 鐵氧體磁珠產品推薦系統")

# 📤 **左側 - PDF 上傳功能**
uploaded_pdf = st.sidebar.file_uploader("上傳鐵氧體磁珠產品規格書 (PDF)", type="pdf")

if uploaded_pdf:
    with st.spinner("⏳ 解析 PDF..."):
        pdf_text = extract_text_from_pdf(uploaded_pdf)
        save_pdf_text_to_db(pdf_text)
        st.sidebar.success("✅ 產品規格書已存入資料庫！")

# 📥 **需求輸入區**
user_input = st.text_area(
    "📝 請輸入您的鐵氧體磁珠需求：", 
    "應用: 抑制大電流電源線上的噪聲。\n"
    "阻抗需求: 在 100MHz 時，阻抗需達到 30Ω ±25%。\n"
    "額定電流: 電源線上的最大直流電流為 10A，因此需要額定電流至少 11000mA 的磁珠。\n"
    "直流電阻: DCR 越低越好，以減少功率損耗。\n"
    "尺寸限制: 可以使用 3216 尺寸的磁珠。\n"
    "工作溫度: 設備工作溫度範圍為 -20℃ 到 +100℃。\n"
    "安規要求: 必須符合 RoHS 規範。"
)

# 🛠 **檢查資料庫是否有產品規格**
product_specs_exist = bool(get_all_product_specs())

if st.button("📌 提交"):
    if not product_specs_exist:
        st.warning("⚠️ 資料庫中無產品規格，請先上傳 PDF。")
    elif not user_input.strip():
        st.warning("⚠️ 請輸入您的需求！")
    else:
        with st.spinner("🤖 AI 代理正在分析並推薦產品..."):
            response = asyncio.run(get_agent_response(user_input))
            st.success("🎯 推薦結果：")
            st.write(response)
