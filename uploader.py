# === 檔案路徑：uploader.py
# === 功能說明：
# 處理 PDF 與 Excel 上傳，並將結構化資料寫入資料庫，支援選擇是否使用 LLM
# === 最後更新：2025-04-13

import streamlit as st
import pdfplumber
import pandas as pd
import asyncio
import zipfile
import tempfile
import os
from database import (
    save_pdf_text_to_db, get_all_product_specs_raw, delete_product_spec_by_id,
    get_all_structured_specs, save_structured_spec_to_db
)
from spec_classifier import classify_specs_from_text
from excel_importer import import_excel_file, import_excel_folder

# === PDF 上傳 ===
def extract_text_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        return "\n".join([page.extract_text() or "" for page in pdf.pages])

def upload_pdf_interface():
    st.subheader("📄 上傳 PDF 產品規格書")
    uploaded_pdf = st.file_uploader("選擇 PDF 檔案", type="pdf", key="pdf_uploader")

    if uploaded_pdf:
        st.info("📄 檔案已選擇，按下按鈕啟動分析")
        if st.button("✅ 確認上傳並啟動分析"):
            with st.spinner("正在擷取 PDF 內容..."):
                text = extract_text_from_pdf(uploaded_pdf)
                save_pdf_text_to_db("LLM", uploaded_pdf.name, text)

                st.success("✅ PDF 上傳成功，內容已儲存")
                st.info("🔍 AI 分析中...")

                try:
                    extracted = asyncio.run(classify_specs_from_text(text))
                except Exception as e:
                    st.error(f"❌ AI 分析錯誤：{e}")
                    return

                count = 0
                vendor_name = ""
                for item in extracted:
                    if "part_number" in item:
                        save_structured_spec_to_db(item, item.get("vendor", "Unknown"), uploaded_pdf.name)
                        vendor_name = item.get("vendor", vendor_name or "Unknown")
                        count += 1

                st.success(f"✅ 完成結構化輸入，共 {count} 筆")
                if vendor_name:
                    st.info(f"📌 依據檔名判斷供應商：**{vendor_name}**")

                with st.expander("📊 結構化資料預覽"):
                    st.dataframe(pd.DataFrame(extracted), use_container_width=True)

# === Excel / ZIP ===
def upload_excel_interface():
    st.subheader("📃 上傳 Excel / ZIP 產品規格")
    use_llm = st.toggle("🤖 使用 LLM 分析欄位", value=True)

    uploaded_file = st.file_uploader("選擇 Excel (.xlsx) 或 ZIP", type=["xlsx", "xls", "zip"], key="excel_uploader")

    if uploaded_file is not None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            with st.spinner("處理中..."):
                try:
                    if uploaded_file.name.endswith(".zip"):
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:
                            zip_ref.extractall(temp_dir)
                        asyncio.run(import_excel_folder(temp_dir, use_llm=use_llm))
                        st.success("✅ ZIP 內 Excel 已全數匯入")
                    else:
                        asyncio.run(import_excel_file(file_path, use_llm=use_llm))
                        st.success("✅ Excel 已匯入")
                except Exception as e:
                    st.error(f"❌ 匯入失敗：{e}")

# === 清單 ===
def show_uploaded_pdfs():
    st.subheader("📄 原始 PDF 列表")
    specs = get_all_product_specs_raw()
    if not specs:
        st.info("尚未上傳任何產品")
        return

    for spec_id, vendor, filename, content, _ in specs:
        with st.expander(f"📘 {vendor} - {filename}"):
            st.text_area("📄 預覽", content[:1000], height=200, disabled=True, key=f"preview_{spec_id}")
            if st.button(f"❌ 刪除 {filename}", key=f"delete_{spec_id}"):
                delete_product_spec_by_id(spec_id)
                st.success(f"已刪除 {filename} 。請重新整理頁面")

# === 結構化 ===
def show_structured_products():
    st.subheader("🛂 結構化產品列表")
    products = get_all_structured_specs()

    if not products:
        st.info("尚無結構化資料")
        return

    df = pd.DataFrame(products)
    vendor_filter = st.selectbox("🔍 供應商篩選", ["全部"] + sorted(df["vendor"].dropna().unique().tolist()))
    file_filter = st.selectbox("📂 來源檔案篩選", ["全部"] + sorted(df["source_filename"].dropna().unique().tolist()))

    filtered_df = df.copy()
    if vendor_filter != "全部":
        filtered_df = filtered_df[filtered_df["vendor"] == vendor_filter]
    if file_filter != "全部":
        filtered_df = filtered_df[filtered_df["source_filename"] == file_filter]

    st.dataframe(filtered_df, use_container_width=True)
