import streamlit as st
import pdfplumber
from database import save_pdf_text_to_db, get_all_product_specs_raw, delete_product_spec_by_id

def extract_text_from_pdf(file):
    """ 使用 pdfplumber 解析 PDF 文本 """
    with pdfplumber.open(file) as pdf:
        text = "\n".join([page.extract_text() or "" for page in pdf.pages])
    return text

def upload_pdf():
    uploaded_pdf = st.file_uploader("上傳鐵氧體磁珠產品規格書 (PDF)", type="pdf")
    if uploaded_pdf:
        with st.spinner("正在解析 PDF..."):
            pdf_text = extract_text_from_pdf(uploaded_pdf)
            save_pdf_text_to_db(uploaded_pdf.name, pdf_text)
            st.success(f"✅ {uploaded_pdf.name} 已儲存至資料庫！")

def show_uploaded_pdfs():
    st.subheader("📑 已上傳的規格書")
    specs = get_all_product_specs_raw()
    if not specs:
        st.info("尚未上傳任何產品規格書。")
        return

    for spec_id, filename, content in specs:
        with st.expander(f"📄 {filename}"):
            st.text_area("預覽內容（前 1000 字）：", content[:1000], height=200, disabled=True)
            if st.button(f"❌ 刪除 {filename}", key=f"delete_{spec_id}"):
                delete_product_spec_by_id(spec_id)
                st.success(f"🗑️ 已刪除 {filename}！請重新整理頁面以查看更新結果。")
