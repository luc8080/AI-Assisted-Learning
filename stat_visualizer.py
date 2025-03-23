# stat_visualizer.py
import streamlit as st
import re
import pandas as pd
import plotly.express as px
from database import get_all_product_specs_raw

def extract_dcr_and_current(text: str) -> list[dict]:
    """
    從原始文本中萃取所有可能的 DCR / current 數值
    支援單位 mA, A, Ω, mΩ
    """
    results = []
    dcr_matches = re.findall(r"DCR.*?([\d\.]+)\s*(m?Ω)", text, flags=re.IGNORECASE)
    current_matches = re.findall(r"(Rated|Current).*?([\d\.]+)\s*(mA|A)", text, flags=re.IGNORECASE)

    for val, unit in dcr_matches:
        try:
            ohm = float(val) / 1000 if unit.lower() == "mω" else float(val)
            results.append({"type": "DCR (Ω)", "value": ohm})
        except:
            continue

    for _, val, unit in current_matches:
        try:
            ma = float(val) * 1000 if unit == "A" else float(val)
            results.append({"type": "Current (mA)", "value": ma})
        except:
            continue

    return results

def plot_histogram(data: list[dict]):
    if not data:
        st.info("尚無可用資料進行統計分析。")
        return

    df = pd.DataFrame(data)

    for param in df["type"].unique():
        sub = df[df["type"] == param]
        fig = px.histogram(
            sub,
            x="value",
            nbins=20,
            title=f"{param} 分布圖",
            labels={"value": param},
            color_discrete_sequence=["#0074D9"]
        )
        fig.update_layout(bargap=0.1)
        st.plotly_chart(fig, use_container_width=True)

def show_pdf_content_stats():
    st.subheader("📊 PDF 規格內容統計（DCR / 電流）")

    raw_files = get_all_product_specs_raw()
    if not raw_files:
        st.info("尚未上傳任何產品規格書。")
        return

    all_data = []
    for _, vendor, filename, content, _ in raw_files:
        extracted = extract_dcr_and_current(content)
        all_data.extend(extracted)

    if all_data:
        st.success(f"共擷取到 {len(all_data)} 筆 DCR / Current 數值")
        plot_histogram(all_data)
    else:
        st.warning("⚠️ 無法從目前 PDF 文本中擷取出有效數值。")
