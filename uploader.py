import streamlit as st
import pdfplumber
from database import save_pdf_text_to_db, get_all_product_specs_raw, delete_product_spec_by_id

def extract_text_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        return "\n".join([page.extract_text() or "" for page in pdf.pages])

def upload_pdf():
    vendor = st.selectbox("📦 選擇產品供應商", ["自家", "Murata", "TDK", "Vishay", "其他"])
    uploaded_pdf = st.file_uploader("📤 上傳鐵氧體磁珠產品規格書 (PDF)", type="pdf")
    if uploaded_pdf:
        with st.spinner("正在解析 PDF..."):
            content = extract_text_from_pdf(uploaded_pdf)
            save_pdf_text_to_db(vendor, uploaded_pdf.name, content)
            st.success(f"✅ {vendor} - {uploaded_pdf.name} 已儲存至資料庫！")

def show_uploaded_pdfs():
    st.subheader("📑 已上傳的規格書")
    specs = get_all_product_specs_raw()
    if not specs:
        st.info("尚未上傳任何產品規格書。")
        return
    for spec_id, vendor, filename, content in specs:
        with st.expander(f"📄 {filename} ({vendor})"):
            st.text_area("預覽內容", content[:1000], height=200, disabled=True)
            if st.button(f"❌ 刪除 {filename}", key=f"delete_{spec_id}"):
                delete_product_spec_by_id(spec_id)
                st.success(f"🗑️ 已刪除 {filename}！請重新整理頁面。")
