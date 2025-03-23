# uploader.py
import streamlit as st
import pdfplumber
from database import save_pdf_text_to_db, get_all_product_specs_raw, delete_product_spec_by_id

def extract_text_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        return "\n".join([page.extract_text() or "" for page in pdf.pages])

def upload_pdf():
    st.subheader("📤 上傳鐵氧體磁珠產品規格書")
    vendor = st.text_input("製造商名稱", key="vendor_input")
    uploaded_pdf = st.file_uploader("選擇 PDF 檔案", type="pdf", key="pdf_uploader")

    if uploaded_pdf and vendor:
        with st.spinner("正在擷取 PDF 文字內容..."):
            text = extract_text_from_pdf(uploaded_pdf)
            save_pdf_text_to_db(vendor, uploaded_pdf.name, text)
            st.success("✅ 上傳完成，內容已儲存至資料庫")
    elif uploaded_pdf and not vendor:
        st.warning("⚠️ 請先輸入製造商名稱")

def show_uploaded_pdfs():
    st.subheader("📄 已上傳的產品規格書")
    specs = get_all_product_specs_raw()
    if not specs:
        st.info("尚未上傳任何產品。")
        return

    for spec_id, vendor, filename, content, _ in specs:
        with st.expander(f"📘 {vendor} - {filename}"):
            st.text_area("📄 規格書內容預覽", content[:1000], height=200, disabled=True, key=f"preview_{spec_id}")
            if st.button(f"❌ 刪除 {filename}", key=f"delete_{spec_id}"):
                delete_product_spec_by_id(spec_id)
                st.success(f"已刪除 {filename}！請重新整理頁面以查看更新。")
