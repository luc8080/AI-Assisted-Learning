import streamlit as st
import pdfplumber
import asyncio
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from dotenv import load_dotenv
import os

load_dotenv()

client = AsyncOpenAI(
    base_url=os.getenv("GOOGLE_GEMINI_ENDPOINT"),
    api_key=os.getenv("GOOGLE_GEMINI_API_KEY")
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

st.title("📘 AI 鐵氧體磁珠 (Ferrite Chip Beads)選擇助手")

# 初始化多個代理
requirement_agent = Agent(
    name="需求分析代理",
    instructions="分析用戶需求，提取關鍵規格（如:Dimension、Material、Impedance、Packaging、Rated Current）。",
    model=model
)

spec_agent = Agent(
    name="規格分析代理",
    instructions="從 PDF 解析產品規格，擷取核心資訊。",
    model=model
)
recommend_agent = Agent(
    name="推薦代理",
    instructions="根據用戶需求與產品規格，推薦最佳產品。",
    model=model
)

# 上傳 PDF
uploaded_file = st.file_uploader("請上傳產品規格書 (PDF)", type=["pdf"])

def extract_text_from_pdf(file):
    """ 使用 pdfplumber 解析 PDF 文本 """
    with pdfplumber.open(file) as pdf:
        text = "\n".join([page.extract_text() or "" for page in pdf.pages])
    return text

# 使用者輸入需求
user_input = st.text_area("請輸入您的鐵氧體磁珠 (Ferrite Chip Beads)需求：", "例如：應用場景、需要 10A 以上的電流，尺寸不得超過 10x10mm")

# 觸發按鈕
if st.button("分析並推薦產品"):
    if not uploaded_file or not user_input:
        st.warning("請確保您已上傳 PDF 並輸入需求")
    else:
        with st.spinner("AI 分析中..."):

            # 解析用戶需求
            user_needs = asyncio.run(Runner.run(requirement_agent, user_input))
            st.write("🔍 需求分析結果：", user_needs.final_output)

            # 解析 PDF 規格
            pdf_text = extract_text_from_pdf(uploaded_file)
            spec_data = asyncio.run(Runner.run(spec_agent, pdf_text))
            st.write("📄 產品規格分析：", spec_data.final_output)

            # 生成產品推薦
            recommendation = asyncio.run(Runner.run(recommend_agent, f"需求: {user_needs.final_output}"))
            st.success("✅ AI 推薦結果：")
            st.write(recommendation.final_output)
