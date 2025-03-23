# app.py
import streamlit as st
from uploader import upload_pdf, show_uploaded_pdfs
from recommendation import process_recommendation
from database import init_db, check_database_status
from ui import show_query_history
from stat_visualizer import show_pdf_content_stats  # 🆕 統計圖模組

def main():
    st.set_page_config(page_title="鐵氧體磁珠產品推薦系統", layout="wide")

    # 初始化資料庫
    init_db()

    # 側邊功能選單
    menu = st.sidebar.radio("📂 功能選單", ["📁 產品規格維護", "🎯 產品推薦", "🧪 查詢紀錄"])

    if menu == "📁 產品規格維護":
        st.title("📁 規格書上傳與管理")
        upload_pdf()
        st.divider()
        show_uploaded_pdfs()
        st.divider()
        show_pdf_content_stats()  # 🆕 顯示 DCR / 電流分布圖

    elif menu == "🎯 產品推薦":
        st.title("🎯 AI 智慧推薦磁珠產品")

        if not check_database_status():
            st.warning("⚠️ 尚未上傳任何產品規格書")
        else:
            process_recommendation(None)

    elif menu == "🧪 查詢紀錄":
        st.title("🧪 歷史查詢紀錄")
        show_query_history()

if __name__ == "__main__":
    main()
