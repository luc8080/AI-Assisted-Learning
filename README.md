# AI-Assisted-Learning
113-2 網路學習輔助系統研究

# 20250309
基於 dataAgent 改寫

待執行
 - 製造商產品規格書待補 (濾波器、鐵氧體磁珠和晶片)(Murata Electronics、Samsung Electro-Mechanics、TAI-TECH Advanced Electronics Co., Ltd.、TDK Corporation)
 - 改用其他 llm 模型
 - 使用 streamlit 設計簡易的使用者互動介面

# 預期效果
## 使用者輸入範例
"用於汽車電源的磁珠，阻抗範圍50-100Ω，額定電流至少3A，符合AEC-Q200標準"

## 系統輸出範例
=== 產品推薦報告 ===
1. Murata BLM15PX471SN1D
   - 阻抗：470Ω±25% @100MHz
   - 額定電流：5A @85°C
   - 認證：AEC-Q200 Grade 1
   - 製造商：Murata

2. Tai-Tech HFZ2012PF-471T25
   - 阻抗：470Ω±25% @100MHz
   - 額定電流：5.5A @85°C
   - 認證：IEC 62368
   - 成本優勢：比方案1低15%

3. ...（其他推薦結果）
