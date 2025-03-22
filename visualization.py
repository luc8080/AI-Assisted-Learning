import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

matplotlib.rcParams['font.family'] = 'Microsoft JhengHei'
matplotlib.rcParams['axes.unicode_minus'] = False

def plot_radar_chart(products):
    labels = ["阻抗 (Ω)", "額定電流 (mA)", "DCR (mΩ)", "溫度範圍 (°C)"]
    values, names = [], []
    for p in products:
        try:
            imp = p.get("impedance", 0)
            cur = p.get("current", 0)
            dcr = p.get("dcr", 0)
            temp = p.get("temp_max", 0) - p.get("temp_min", 0)
            values.append([imp, cur, -dcr, temp])
            names.append(f"{p['name']} ({p['vendor']})")
        except: continue
    if not values: return
    values = np.array(values)
    norm = (values - values.min(0)) / (values.max(0) - values.min(0) + 1e-6)
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist() + [0]
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    for i, val in enumerate(norm):
        data = val.tolist() + [val[0]]
        ax.plot(angles, data, label=names[i])
        ax.fill(angles, data, alpha=0.1)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    st.pyplot(fig)

def plot_match_score_bar_chart(products, user_req):
    scores, labels = [], []
    for p in products:
        score = 0
        if user_req.get("impedance") * (1 - user_req.get("impedance_tolerance", 0.25)) <= p.get("impedance", 0) <= user_req.get("impedance") * (1 + user_req.get("impedance_tolerance", 0.25)):
            score += 1
        if p.get("current", 0) >= user_req.get("current", 0):
            score += 1
        if p.get("dcr", 9999) <= user_req.get("dcr", 9999):
            score += 1
        percent = round(score / 3 * 100)
        scores.append(percent)
        labels.append(f"{p['name']} ({p['vendor']})")
    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.barh(labels, scores, color="skyblue")
    ax.set_xlim(0, 100)
    for bar in bars:
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, f"{bar.get_width()}%", va='center')
    st.pyplot(fig)

def plot_comparison_radar_chart(competitor_name, competitor_text, products):
    labels = ["阻抗 (Ω)", "額定電流 (mA)", "DCR (mΩ)", "溫度範圍 (°C)"]
    comp_data = {"impedance": 30, "current": 10000, "dcr": 2.5, "temp_min": -20, "temp_max": 100}
    comp_vector = [comp_data["impedance"], comp_data["current"], -comp_data["dcr"], comp_data["temp_max"] - comp_data["temp_min"]]
    values = [comp_vector]
    names = [f"{competitor_name}（競品）"]
    for p in products:
        try:
            values.append([
                p.get("impedance", 0),
                p.get("current", 0),
                -p.get("dcr", 0),
                p.get("temp_max", 0) - p.get("temp_min", 0)
            ])
            names.append(f"{p['name']} ({p['vendor']})")
        except: continue
    values = np.array(values)
    norm = (values - values.min(0)) / (values.max(0) - values.min(0) + 1e-6)
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist() + [0]
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    for i, val in enumerate(norm):
        data = val.tolist() + [val[0]]
        ax.plot(angles, data, label=names[i])
        ax.fill(angles, data, alpha=0.1)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels)
    ax.set_title("競品 vs 自家產品雷達圖")
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    st.pyplot(fig)
