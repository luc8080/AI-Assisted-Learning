import streamlit as st
from uploader import upload_pdf, show_uploaded_pdfs
from recommendation import process_recommendation, compare_and_recommend
from database import check_database_status, init_db
from ui import show_query_history

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

        st.header("🔍 選擇推薦模式")
        mode = st.radio("請選擇推薦模式：", ["🧠 自然語言需求推薦", "📎 競品比對推薦"])

        if mode == "🧠 自然語言需求推薦":
            process_recommendation(None)
        elif mode == "📎 競品比對推薦":
            part_number = st.text_input("請輸入競品料號（例如：BLM31KN601）")
            if st.button("比對並推薦自家產品"):
                if part_number:
                    compare_and_recommend(part_number)
                else:
                    st.warning("請輸入競品料號")

        show_query_history()

if __name__ == "__main__":
    main()
