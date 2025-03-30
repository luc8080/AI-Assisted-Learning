# 🧠 AI 產品推薦系統

本系統結合 OpenAI Agents SDK、Streamlit 與 SQLite，協助使用者從 PDF 產品規格書中找出最適合的產品，支援自然語言推薦、競品比對推薦與互動式視覺化比較。

---

## 📦 專案模組一覽

| 檔案 / 模組名稱       | 功能說明 |
|------------------------|----------|
| `app.py`               | 主應用程式入口，整合所有功能模組與使用流程 |
| `database.py`          | 資料庫初始化與管理，包含規格書與查詢紀錄 |
| `uploader.py`          | PDF 規格書上傳、解析、預覽與刪除 |
| `recommendation.py`    | 產品推薦主流程，自然語言與競品模式皆可執行 |
| `requirement_flow.py`  | AI 多輪對話需求釐清與補問流程控制 |
| `spec_extractor.py`    | 使用 LLM 將表格 row 轉為結構化產品規格 dict |
| `table_parser.py`      | 從 PDF 表格中擷取指定料號的規格資料 |
| `visualization.py`     | 繪製雷達圖、條件達成率等互動式視覺化圖表 |
| `stat_visualizer.py`   | 根據純文字內容分析 DCR 與電流分布圖（統計視覺化） |
| `ui.py`                | UI 區塊組件，如需求輸入、查詢紀錄、側邊欄元件等 |
| `requirements.txt`     | 所有依賴套件清單（含 Streamlit、Agents SDK 等） |
| `product_specs.db`     | SQLite 資料庫檔案，儲存產品內容與查詢紀錄 |

---

## 🚀 功能特色

### 🧠 AI 產品推薦（自然語言模式）
- 使用者輸入如「10A 電流、100MHz 阻抗」的需求
- AI 解析條件 → 從 PDF 資料庫比對規格 → 推薦產品

### 🔁 競品比對推薦
- 輸入競品料號（如 Murata 型號）
- 從 PDF 表格擷取 row → 分析規格 → 推薦對應自家產品

### 📊 視覺化比較（Plotly）
- 雷達圖：推薦產品與競品的多維規格比較
- 條件達成率圖：視覺化每款產品與需求的匹配度
- DCR / 電流分布圖：從 PDF 文本自動統計繪製

### 📂 PDF 規格管理
- 上傳 PDF、自動解析文字並存入 DB
- 可預覽與刪除已上傳規格書
- 支援多家供應商規格管理

### 🗂️ 查詢紀錄保存
- 自動儲存使用者需求與 AI 回覆
- 可從側邊欄查詢歷史紀錄

---

## 📌 安裝與啟動

```bash
# 建立虛擬環境並安裝套件
python -m venv .venv
source .venv/bin/activate      # Windows 請使用 .venv\Scripts\activate
pip install -r requirements.txt

# 啟動應用
streamlit run app.py

#.env 設定範例
GOOGLE_GEMINI_ENDPOINT=https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-pro:generateContent
GOOGLE_GEMINI_API_KEY=你的_API_Key

# 資料庫資料表
product_specs	儲存每份 PDF 的文字內容、來源供應商、後續可擴充結構化規格
query_history	儲存使用者查詢紀錄與 AI 回覆內容

# 未來可擴充功能
自動轉換 PDF 表格為結構化規格資料（JSON）
推薦排序設定（如 DCR 最低優先）
多角色權限登入（研發 / 採購 / 系統管理員）
匯出推薦報告（PDF / CSV）