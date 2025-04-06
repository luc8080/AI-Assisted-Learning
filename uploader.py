import streamlit as st
import pdfplumber
import asyncio
import pandas as pd
from database import (
    save_pdf_text_to_db, get_all_product_specs_raw, delete_product_spec_by_id,
    save_structured_spec_to_db, get_all_structured_specs
)
from spec_classifier import classify_specs_from_text

def extract_text_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        return "\n".join([page.extract_text() or "" for page in pdf.pages])

def upload_pdf():
    st.subheader("📤 上傳產品規格書（自動結構化與分類）")
    uploaded_pdf = st.file_uploader("選擇 PDF 檔案", type="pdf", key="pdf_uploader")

    if uploaded_pdf:
        st.info("📝 檔案已選擇，請按下下方按鈕開始處理")

        if st.button("✅ 確認上傳並啟動分析"):
            with st.spinner("正在擷取 PDF 內容..."):
                text = extract_text_from_pdf(uploaded_pdf)
                save_pdf_text_to_db("LLM", uploaded_pdf.name, text)

                st.success("✅ PDF 上傳成功，內容已儲存至資料庫")
                st.info("🔍 AI 正在解析產品規格與貼分類標籤...")

                try:
                    extracted = asyncio.run(classify_specs_from_text(text))
                except Exception as e:
                    st.error(f"❌ 規格分析錯誤：{e}")
                    return

                if not extracted:
                    st.warning("⚠️ AI 無法從此份 PDF 中擷取出產品規格資料。請確認內容格式。")
                    return

                count = 0
                vendor_name = ""
                for item in extracted:
                    if "part_number" in item:
                        save_structured_spec_to_db(item, item.get("vendor", "Unknown"), uploaded_pdf.name)
                        vendor_name = item.get("vendor", vendor_name or "Unknown")
                        count += 1

                st.success(f"✅ 完成結構化匯入，共擷取 {count} 筆產品資料")
                if vendor_name:
                    st.info(f"📌 自動判斷供應商為：**{vendor_name}**")

                with st.expander("📊 結構化資料預覽"):
                    df = pd.DataFrame(extracted)
                    st.dataframe(df, use_container_width=True)

def show_uploaded_pdfs():
    st.subheader("📄 原始規格書列表（PDF 內容）")
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

def show_structured_products():
    st.subheader("📦 結構化產品清單")
    products = get_all_structured_specs()

    if not products:
        st.info("尚無結構化產品資料。")
        return

    df = pd.DataFrame(products)

    # 篩選功能
    vendor_filter = st.selectbox("🔍 篩選供應商", ["全部"] + sorted(df["vendor"].dropna().unique().tolist()))
    file_filter = st.selectbox("📂 篩選來源檔案", ["全部"] + sorted(df["source_filename"].dropna().unique().tolist()))

    filtered_df = df.copy()
    if vendor_filter != "全部":
        filtered_df = filtered_df[filtered_df["vendor"] == vendor_filter]
    if file_filter != "全部":
        filtered_df = filtered_df[filtered_df["source_filename"] == file_filter]

    st.dataframe(filtered_df, use_container_width=True)
