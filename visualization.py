import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

def plot_recommendation_radar(products: list[dict], competitor_spec: dict = None):
    st.subheader("📊 推薦產品雷達圖（互動式）")

    if not products:
        st.info("⚠️ 無推薦產品可比較")
        return

    metrics = ["impedance", "current", "dcr", "temp_min", "temp_max"]
    labels = {
        "impedance": "阻抗 (Ω)",
        "current": "電流 (mA)",
        "dcr": "DCR (Ω)",
        "temp_min": "最低溫 (°C)",
        "temp_max": "最高溫 (°C)"
    }

    fig = go.Figure()

    def normalize(value_list, inverse=False):
        arr = np.array(value_list, dtype=np.float64)
        norm = (arr - arr.min()) / (arr.max() - arr.min() + 1e-9)
        return 1 - norm if inverse else norm

    data = pd.DataFrame(products)
    data["label"] = data["part_number"].fillna("產品")

    for metric in metrics:
        if metric not in data.columns:
            data[metric] = 0

    for metric in metrics:
        inv = (metric == "dcr")
        data[metric + "_norm"] = normalize(data[metric], inverse=inv)

    for i, row in data.iterrows():
        fig.add_trace(go.Scatterpolar(
            r=row[[m + "_norm" for m in metrics]],
            theta=[labels[m] for m in metrics],
            fill='toself',
            name=row["label"]
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1])
        ),
        showlegend=True,
        title="規格雷達圖比較"
    )

    st.plotly_chart(fig, use_container_width=True)

def plot_condition_match_bar(requirements: dict, products: list[dict]):
    st.subheader("📋 條件達成率分析（互動式）")

    def match_score(product: dict, req: dict) -> float:
        score = 0
        total = 0
        if req.get("impedance") is not None and product.get("impedance") is not None:
            tolerance = req.get("impedance_tolerance", 0.25)
            if abs(product["impedance"] - req["impedance"]) <= tolerance * req["impedance"]:
                score += 1
            total += 1
        if req.get("current") is not None and product.get("current") is not None:
            if product["current"] >= req["current"]:
                score += 1
            total += 1
        if req.get("dcr") is not None and product.get("dcr") is not None:
            if product["dcr"] <= req["dcr"]:
                score += 1
            total += 1
        if req.get("temp_min") is not None and product.get("temp_min") is not None:
            if product["temp_min"] <= req["temp_min"]:
                score += 1
            total += 1
        if req.get("temp_max") is not None and product.get("temp_max") is not None:
            if product["temp_max"] >= req["temp_max"]:
                score += 1
            total += 1
        return round(score / total * 100, 2) if total else 0.0

    scores = [(p.get("part_number", f"產品{i+1}"), match_score(p, requirements)) for i, p in enumerate(products)]
    df = pd.DataFrame(scores, columns=["產品名稱", "條件達成率 (%)"])
    df = df.sort_values(by="條件達成率 (%)", ascending=False)

    fig = px.bar(
        df,
        x="產品名稱",
        y="條件達成率 (%)",
        text="條件達成率 (%)",
        color="條件達成率 (%)",
        color_continuous_scale="Blues"
    )
    fig.update_layout(title="每個產品的條件匹配程度", yaxis_range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 條件符合度明細表"):
        st.dataframe(df, use_container_width=True)
