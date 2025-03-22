import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

# 設定中文字型以避免字型缺失錯誤
matplotlib.rcParams['font.family'] = 'Microsoft JhengHei'  # Windows 可用
# 如果在 Mac，可改為：'Apple LiGothic Medium'
# 如果在 Linux / Google Colab，可改為：'Noto Sans CJK TC'
matplotlib.rcParams['axes.unicode_minus'] = False  # 正負號也支援

def plot_radar_chart(products):
    labels = ["阻抗 (Ω)", "額定電流 (mA)", "DCR (mΩ)", "工作溫度範圍 (°C)"]
    num_vars = len(labels)

    def normalize(values):
        max_vals = np.max(values, axis=0)
        min_vals = np.min(values, axis=0)
        return (values - min_vals) / (max_vals - min_vals + 1e-6)

    values = []
    names = []
    for p in products:
        try:
            impedance = float(p.get("impedance", 0))
            current = float(p.get("current", 0))
            dcr = float(p.get("dcr", 0))
            temp_range = float(p.get("temp_max", 0)) - float(p.get("temp_min", 0))
        except:
            continue
        values.append([impedance, current, -dcr, temp_range])
        names.append(p.get("name", "Unnamed"))

    if not values:
        st.warning("⚠️ 無法解析產品資料繪製雷達圖。")
        return

    values = np.array(values)
    normalized = normalize(values)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))

    for i, val in enumerate(normalized):
        data = val.tolist() + val[:1].tolist()
        ax.plot(angles, data, label=names[i])
        ax.fill(angles, data, alpha=0.1)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels)
    ax.set_title("推薦產品規格雷達圖", size=14)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    st.pyplot(fig)
