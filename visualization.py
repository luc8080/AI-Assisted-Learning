# visualization.py
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def plot_recommendation_radar(products: list[dict], competitor_spec: dict = None):
    st.subheader("📊 推薦產品雷達圖比較")

    if not products:
        st.info("⚠️ 無推薦產品可比較")
        return

    metrics = ["impedance", "current", "dcr", "temp_min", "temp_max"]
    labels = ["阻抗", "額定電流", "DCR", "最低溫", "最高溫"]

    def normalize_metric(metric, values):
        arr = np.array(values, dtype=np.float64)
        if metric == "dcr":
            arr = np.max(arr) - arr  # DCR 越小越好
        return (arr - arr.min()) / (arr.max() - arr.min() + 1e-9)

    data = []
    names = []

    for p in products:
        row = [p.get(m, 0) for m in metrics]
        data.append(row)
        names.append(p.get("name", f"產品{len(data)}"))

    if competitor_spec:
        competitor_row = [competitor_spec.get(m, 0) for m in metrics]
        data.append(competitor_row)
        names.append("🏴 競品")

    data = np.array(data)
    normalized = np.array([normalize_metric(m, data[:, i]) for i, m in enumerate(metrics)]).T

    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    for i, row in enumerate(normalized):
        values = row.tolist() + row[:1].tolist()
        ax.plot(angles, values, label=names[i])
        ax.fill(angles, values, alpha=0.1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_title("推薦產品比較", fontsize=14)
    ax.legend(loc="best", bbox_to_anchor=(1.2, 1.1))
    st.pyplot(fig)

def plot_condition_match_bar(requirements: dict, products: list[dict]):
    st.subheader("📋 條件達成率分析")

    def match_score(product: dict, req: dict) -> float:
        score = 0
        total = 0
        if "impedance" in req and "impedance" in product:
            if abs(product["impedance"] - req["impedance"]) <= req.get("impedance_tolerance", 0.25) * req["impedance"]:
                score += 1
            total += 1
        if "current" in req and "current" in product:
            if product["current"] >= req["current"]:
                score += 1
            total += 1
        if "dcr" in req and "dcr" in product:
            if product["dcr"] <= req["dcr"]:
                score += 1
            total += 1
        if "temp_min" in req and "temp_min" in product:
            if product["temp_min"] <= req["temp_min"]:
                score += 1
            total += 1
        if "temp_max" in req and "temp_max" in product:
            if product["temp_max"] >= req["temp_max"]:
                score += 1
            total += 1
        return round(score / total * 100, 2) if total else 0.0

    scores = [(p.get("name", f"產品{i+1}"), match_score(p, requirements)) for i, p in enumerate(products)]
    scores.sort(key=lambda x: x[1], reverse=True)

    df = pd.DataFrame(scores, columns=["產品名稱", "條件達成率 (%)"])
    st.bar_chart(df.set_index("產品名稱"))

    with st.expander("📋 條件符合度明細"):
        st.dataframe(df, use_container_width=True)
