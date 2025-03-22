# app.py
import streamlit as st
from uploader import upload_pdf
from recommendation import process_recommendation
from database import check_database_status, init_db
from ui import show_query_history, show_user_input_section


def main():
    st.set_page_config(page_title="鐵氧體磁珠產品推薦系統", layout="wide")

    # 初始化資料庫
    init_db()

    # Sidebar for file upload
    st.sidebar.title("📂 上傳產品規格書")
    upload_pdf()

    # Check database status
    if not check_database_status():
        st.sidebar.warning("⚠️ 資料庫中無產品規格書，請先上傳 PDF。")
        return

    # Display user input section
    user_input = show_user_input_section()

    # Process recommendation
    if st.button("提交"):
        if user_input:
            process_recommendation(user_input)
        else:
            st.warning("請輸入您的需求！")

    # Display query history
    show_query_history()


if __name__ == "__main__":
    main()