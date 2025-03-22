import streamlit as st
from uploader import upload_pdf, show_uploaded_pdfs
from recommendation import process_recommendation
from database import check_database_status, init_db
from ui import show_query_history, show_user_input_section

def main():
    st.set_page_config(page_title="鐵氧體磁珠產品推薦系統", layout="wide")
    init_db()

    menu = st.sidebar.radio("功能選單", ["📁 產品規格維護", "🎯 產品推薦"])

    if menu == "📁 產品規格維護":
        st.header("📤 上傳產品規格書")
        upload_pdf()
        st.divider()
        show_uploaded_pdfs()

    elif menu == "🎯 產品推薦":
        if not check_database_status():
            st.warning("⚠️ 資料庫中無產品規格書，請先至 [產品規格維護] 上傳 PDF。")
            return

        user_input = show_user_input_section()

        if st.button("🚀 提交需求並取得推薦"):
            if user_input.strip():
                process_recommendation(user_input)
            else:
                st.warning("請輸入您的需求！")

        show_query_history()

if __name__ == "__main__":
    main()
