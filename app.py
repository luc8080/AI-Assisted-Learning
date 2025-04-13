# === 檔案路徑：app.py
# === 功能說明：
# 主畫面入口，整合 PDF/Excel 上傳、推薦系統與產品管理。
# === 最後更新：2025-04-13

import streamlit as st
from uploader import (
    upload_pdf_interface,
    upload_excel_interface,
    show_uploaded_pdfs,
    show_structured_products
)
from recommendation import process_recommendation
from database import init_db

# 初始化資料庫
init_db()

# 設定頁面基本屬性
st.set_page_config(page_title="Tai-Tech AI 磁性元件推薦系統", layout="wide")

# 主流程
def main():
    st.title("Tai-Tech AI 磁性元件推薦系統")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📄 PDF 上傳", "📊 Excel 規格匯入", "🎯 AI 產品推薦", "📦 結構化產品瀏覽"
    ])

    with tab1:
        upload_pdf_interface()

    with tab2:
        upload_excel_interface()

    with tab3:
        process_recommendation(None)

    with tab4:
        show_uploaded_pdfs()
        st.divider()
        show_structured_products()

# 執行主程式
if __name__ == "__main__":
    main()
