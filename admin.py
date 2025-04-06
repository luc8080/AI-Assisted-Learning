import streamlit as st
import pandas as pd
from database import get_all_structured_specs, delete_structured_spec_by_id

def manage_structured_products():
    st.subheader("🧰 結構化產品資料後台管理")

    products = get_all_structured_specs()
    if not products:
        st.info("尚無資料")
        return

    df = pd.DataFrame(products)
    df["操作"] = "❌ 刪除"

    # 選擇供應商與檔案名篩選
    vendor_filter = st.selectbox("🔍 篩選供應商", ["全部"] + sorted(df["vendor"].dropna().unique().tolist()))
    file_filter = st.selectbox("📂 篩選來源檔案", ["全部"] + sorted(df["source_filename"].dropna().unique().tolist()))

    if vendor_filter != "全部":
        df = df[df["vendor"] == vendor_filter]
    if file_filter != "全部":
        df = df[df["source_filename"] == file_filter]

    for _, row in df.iterrows():
        with st.expander(f"📦 {row['part_number']} | {row['vendor']}"):
            st.write(row.drop("操作").to_dict())
            if st.button(f"❌ 刪除 {row['part_number']}", key=f"delete_{row['id']}"):
                delete_structured_spec_by_id(row["id"])
                st.success("已刪除，請重新整理以查看更新")
