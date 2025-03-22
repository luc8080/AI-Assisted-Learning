# uploader.py
import streamlit as st
import pdfplumber
from database import save_pdf_text_to_db

def extract_text_from_pdf(file):
    """ 使用 pdfplumber 解析 PDF 文本 """
    with pdfplumber.open(file) as pdf:
        text = "\n".join([page.extract_text() or "" for page in pdf.pages])
    return text

def upload_pdf():
    uploaded_pdf = st.sidebar.file_uploader("上傳鐵氧體磁珠產品規格書 (PDF)", type="pdf")
    if uploaded_pdf:
        with st.spinner("正在解析 PDF..."):
            pdf_text = extract_text_from_pdf(uploaded_pdf)
            save_pdf_text_to_db(pdf_text)
            st.sidebar.success("產品規格書已存入資料庫！")
