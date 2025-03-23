# app.py
import streamlit as st
from uploader import upload_pdf, show_uploaded_pdfs
from recommendation import process_recommendation
from database import init_db, check_database_status
from ui import show_query_history

def main():
    st.set_page_config(page_title="鐵氧體磁珠產品推薦系統", layout="wide")

    # ✅ 初始化資料庫
    init_db()

    # 📂 左側選單
    menu = st.sidebar.radio("📂 功能選單", ["📁 產品規格維護", "🎯 產品推薦", "🧪 查詢紀錄"])

    if menu == "📁 產品規格維護":
        st.title("📁 規格書上傳與管理")
        upload_pdf()
        st.divider()
        show_uploaded_pdfs()

    elif menu == "🎯 產品推薦":
        st.title("🎯 AI 智慧推薦磁珠產品")

        if not check_database_status():
            st.warning("⚠️ 系統中尚無產品資料，請先上傳 PDF")
            return

        process_recommendation(None)

    elif menu == "🧪 查詢紀錄":
        st.title("🧪 歷史查詢紀錄")
        show_query_history()

if __name__ == "__main__":
    main()
