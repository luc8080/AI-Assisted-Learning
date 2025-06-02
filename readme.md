
---

## 素養導向學習助理 AI 系統

* 本專案是一套專為台灣國高中素養導向題型所設計的互動式 AI 學習助理平台。
* 結合 Streamlit 前端、Python 後端與 SQLite 輕量資料庫，具備即時出題、個人化診斷、學習歷程紀錄、錯題重練、AI 教練互動、題庫維護等功能，支援學生、教師與管理員多角色切換，強調 AI Agents 模組化分工與彈性擴充。
* https://youtu.be/ijhsZ5rC8S4
---

## 目錄

- [素養導向學習助理 AI 系統](#素養導向學習助理-ai-系統)
- [目錄](#目錄)
- [專案簡介](#專案簡介)
- [主要功能](#主要功能)
  - [學生端](#學生端)
  - [教師／管理端](#教師管理端)
  - [輔助／進階](#輔助進階)
- [系統架構](#系統架構)
- [目錄結構說明](#目錄結構說明)
- [安裝與啟動方式](#安裝與啟動方式)
  - [1. 安裝環境](#1-安裝環境)
  - [2. 初始化資料庫](#2-初始化資料庫)
  - [3. 啟動系統](#3-啟動系統)
- [資料流程與運作說明](#資料流程與運作說明)
- [維護與擴充建議](#維護與擴充建議)

---

## 專案簡介

* 本專案旨在解決傳統學習平台難以針對個別學生即時診斷學習弱點與提供個人化回饋的痛點。
* 透過多個 AI Agents（如：診斷、教練、出題、資料維護等），學生可得到動態的錯題分析與學習建議，教師則能掌握學生成效並維護題庫內容，系統整體設計符合素養導向評量的數位教學趨勢。

---

## 主要功能

### 學生端

* **出題/作答（task\_view）**：自選題組即時練習，支援自動批改。
* **錯題本（wrongbook\_view）**：自動收錄錯題，便於針對性重練。
* **學習歷程紀錄（summary\_view）**：可視化統計作答紀錄與學習成效。
* **AI 智能診斷（ai\_diagnosis\_view）**：根據答題行為給出個人化補強建議。
* **AI 教練互動（coach\_chat\_view）**：模擬真人教練即時提問與引導。

### 教師／管理端

* **題庫管理（question\_bank\_maintain\_view, question\_maintain\_view）**：維護題組與題目資料。
* **題目補強與分類（question\_enrich\_view, topic\_classify\_view）**：手動補充題目欄位與主題標註。

### 輔助／進階

* **多 Agent 協作流程（handoff\_view）**：實驗型任務協作展示。
* **學習歷程摘要產生（learning\_summary\_agent.py）**。
* **RAG 知識查詢工具（rag\_tools/knowledge\_lookup.py）**。

---

## 系統架構

使用者
↓
Streamlit 前端介面（interface/\*\_view\.py）
↓
AI Agents 核心（assistant\_core/\*.py, coach/, feedback/ 等）
↓
資料層：SQLite 題庫/用戶紀錄（data\_store/、database/）

* 前端採用 Streamlit，提供直覺的網頁互動介面。
* 後端以 Python 分層設計，AI Agent 模組可獨立擴充。
* 所有數據存取、紀錄與查詢皆以本地 SQLite 管理。

---

## 目錄結構說明

```text
learning_assistant/
├── main.py
├── init_db.py
├── init_user_db.py
├── requirements.txt
│
├── interface/
│   ├── ai_diagnosis_view.py
│   ├── coach_chat_view.py
│   ├── handoff_view.py
│   ├── login_view.py
│   ├── question_bank_maintain_view.py
│   ├── question_enrich_view.py
│   ├── question_maintain_view.py
│   ├── summary_view.py
│   ├── task_view.py
│   ├── topic_classify_view.py
│   └── wrongbook_view.py
│
├── assistant_core/
│   ├── ai_diagnosis_agent.py
│   ├── coach_agent.py
│   ├── explain_question.py
│   ├── learning_summary_agent.py
│   ├── llm_generate_questions.py
│   ├── populate_difficulty.py
│   ├── populate_explanations.py
│   ├── populate_keywords.py
│   ├── populate_paragraphs.py
│   ├── populate_question_topics.py
│   ├── coach/
│   ├── feedback/
│   ├── recommendation/
│   └── strategies/
│
├── data_store/
│   ├── question_group_loader.py
│   ├── question_loader.py
│   └── update_answers.py
│
├── database/
│   ├── alter_questions_table.sql
│   └── init_database.sql
│
├── helpers/
│   ├── json_to_sqlite.py
│   └── parse_pdf.py
│
├── models/
│   └── student_model.py
│
├── rag_tools/
│   └── knowledge_lookup.py
│
└── data/、data_store/
```

---

## 安裝與啟動方式

### 1. 安裝環境

* Python 3.9+
* 建議於虛擬環境 (venv/conda) 安裝

```bash
git clone https://github.com/你的帳號/learning_assistant.git
cd learning_assistant
pip install -r requirements.txt
```

### 2. 初始化資料庫

```bash
python init_db.py         # 建立題庫資料庫
python init_user_db.py    # 建立用戶資料庫
```

### 3. 啟動系統

```bash
streamlit run main.py
```

---

## 資料流程與運作說明

1. **登入／身分驗證**：用戶先登入（支援學生、教師、管理員）。
2. **主選單分流**：依據身分進入各功能（作答、診斷、歷程、教練、題庫維護等）。
3. **互動／運算流程**：

   * 前端頁面蒐集用戶輸入，觸發 AI Agent（如診斷、教練、補強）。
   * AI Agent 運算結果存回資料庫，並同步於介面即時呈現。
   * 所有學習紀錄、作答、診斷、建議均可於歷程中查詢與再利用。
4. **資料批次管理／補強**：

   * 題庫匯入、欄位補充、解析產生等，可由各類 populate\_\*.py、data\_store/ 與 helpers/ 目錄下工具腳本完成。
   * 支援 PDF 題目解析、JSON 轉 SQLite 批次載入。

---

## 維護與擴充建議

* 功能頁面皆以單頁模組設計，開發新功能或隱藏不需功能非常方便。
* AI Agent 各自獨立，易於加掛新模型、微調診斷/互動邏輯。
* 資料庫預設為 SQLite，如需擴充可依需求改接 MySQL/PostgreSQL，但資料表設計需同步調整。
* 資料補強（populate\_xxx.py）建議於題庫建置或大規模資料補充時執行，操作前請先備份。
* 進階功能（RAG、Agent 協作、摘要產生），預設屬於實驗模組，可依需求整合至主流程。

---
