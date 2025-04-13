# === 檔案路徑：spec_classifier.py
# === 功能說明：
# 使用 Gemini 模型將原始 PDF 文字解析為產品規格 list[dict]。
# 包含欄位標準化、異常回傳防呆處理。
# === 最後更新：2025-04-13

import os
import json
from dotenv import load_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel

load_dotenv()
client = AsyncOpenAI(
    base_url=os.getenv("GOOGLE_GEMINI_ENDPOINT"),
    api_key=os.getenv("GOOGLE_GEMINI_API_KEY")
)
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

spec_parser_agent = Agent(
    name="SpecClassifier",
    instructions="""
你是一位資深磁性元件工程師，專門負責從 PDF 規格書中解析產品規格並轉為結構化資料。

請根據輸入的文字內容，萃取所有可辨識的產品規格，輸出格式為 list[dict]，每個 dict 表示一筆產品。請注意：

- 若有表格型產品資訊，請轉為如下欄位：
  - part_number
  - impedance（Ω）
  - dcr（Ω）
  - current（mA）
  - size（封裝尺寸）
  - application（如：Automotive、Industrial）
  - temp_min / temp_max（操作溫度範圍）
  - vendor（品牌）
  - source_filename（來源檔名，請用 "from_text_input.pdf"）

- 若找不到任何產品，請回傳空陣列 []

請只回傳純 JSON 陣列（list of dict），不要加任何說明文字。
""",
    model=model
)

async def classify_specs_from_text(text: str) -> list[dict]:
    try:
        result = await Runner.run(agent=spec_parser_agent, input=text)
        raw = result.get_final_output()

        if not raw or not isinstance(raw, str):
            print("[SpecClassifier] ⚠️ LLM 回傳為空或非字串格式")
            return []

        # print(raw[:300])  # ⬅️ 除錯用：可印出前段 JSON 回傳
        parsed = json.loads(raw)

        if not isinstance(parsed, list):
            print("[SpecClassifier] ⚠️ 回傳格式非 list")
            return []

        cleaned = []
        for item in parsed:
            if isinstance(item, dict) and "part_number" in item:
                item.setdefault("vendor", "Unknown")
                item.setdefault("source_filename", "from_text_input.pdf")
                cleaned.append(item)

        return cleaned

    except Exception as e:
        print(f"[SpecClassifier] ❌ JSON 解析失敗：{e}")
        return []
