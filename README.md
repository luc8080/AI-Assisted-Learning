# 🧠 AI 產品推薦系統

這是一套 AI 驅動的產品推薦平台，支援使用者上傳產品的 PDF 規格書，並透過 AI 釐清需求、推薦最適合的產品，並進行條件匹配分析與視覺化。
🚀 支援 LLM 智能推薦 + 結構化資料篩選雙重引擎

---

⚙️ 技術架構

技術	用途
Streamlit	UI 前端與互動控制
SQLite	本地化資料儲存
OpenAI Agents SDK + Gemini	需求釐清、產品推薦、資料分類、規格萃取
pdfplumber	PDF 文本與表格處理
Plotly	推薦視覺化圖表（雷達圖、柱狀圖）
Python 3.10+	主程式語言

---
## 📁 專案結構

├── app.py                       # Streamlit 主頁面入口
├── database.py                 # 所有資料庫 CRUD 操作
├── uploader.py                 # PDF 上傳與預覽、刪除
├── table_parser.py             # PDF 表格解析器（欄位標準化）
├── spec_extractor.py           # 從單筆資料擷取產品規格（LLM）
├── batch_spec_extractor.py     # 從整份 PDF 文本批次萃取多筆產品規格
├── recommendation.py           # 使用需求 + 結構化資料推薦產品（LLM）
├── requirement_flow.py         # 與使用者釐清需求的對話流程
├── visualization.py            # 雷達圖 / 條件匹配視覺化圖表
├── stat_visualizer.py          # 所有 PDF 的 DCR / Current 統計分布圖
├── llm_categorizer.py          # 自動分類 PDF 的供應商 / 類別 / 應用場域
├── ui.py                       # 查詢歷史紀錄與需求輸入欄位
├── migrate_structured_specs_from_texts.py  # 一次性導入舊資料的遷移腳本
└── .env                        # 儲存 API 金鑰與環境變數

---

📦 資料庫結構

使用 SQLite（product_specs.db）包含三張表：

product_specs：原始上傳的 PDF 文本

query_history：查詢紀錄（需求與推薦結果）

structured_specs：經由 LLM 萃取出的產品結構化規格資訊（推薦依據）

---

## 📌 安裝與啟動

# 建立虛擬環境並安裝套件
python -m venv .venv
source .venv/bin/activate      # Windows 請使用 .venv\Scripts\activate
pip install -r requirements.txt

# 啟動應用
streamlit run app.py

#.env 設定範例
GOOGLE_GEMINI_ENDPOINT=https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-pro:generateContent
GOOGLE_GEMINI_API_KEY=你的_API_Key
