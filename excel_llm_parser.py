# === 檔案路徑：excel_llm_parser.py
# === 功能說明：
# 使用 Gemini 模型將 Excel 中的單行 row（Series）轉換為結構化 dict
# 自動判斷欄位（如 impedance, dcr, current 等）並標準化
# === 最後更新：2025-04-13

import os
import json
import pandas as pd
from dotenv import load_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel

# === 初始化 Gemini 模型 ===
load_dotenv()
client = AsyncOpenAI(
    base_url=os.getenv("GOOGLE_GEMINI_ENDPOINT"),
    api_key=os.getenv("GOOGLE_GEMINI_API_KEY")
)
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

# === LLM 代理人設定 ===
excel_row_parser = Agent(
    name="ExcelRowParser",
    instructions="""
你是一位資深的磁性元件應用工程師，專門處理 Excel 中的產品資料行，協助轉換為結構化規格。

請參考以下規則：
- 每次輸入都是單一筆產品資料 row，以 JSON 物件格式呈現（欄位名稱可能不一致）
- 請根據欄位內容推測以下標準欄位：
  - part_number（料號）
  - impedance（阻抗，單位：Ω）
  - dcr（直流電阻，單位：Ω）
  - current（額定電流，單位：mA）
  - test_frequency（測試頻率 MHz）
  - size（尺寸，如 0603, 1206 等）

❗請只回傳格式正確的 JSON dict，勿加入任何說明。
""",
    model=model
)

# === 轉換單一 row 為 dict（用於匯入資料庫） ===
def parse_spec_row_with_llm(row: pd.Series) -> dict:
    row_dict = row.dropna().astype(str).to_dict()
    prompt = f"請協助解析以下產品資料：\n{json.dumps(row_dict, ensure_ascii=False)}"

    try:
        result = Runner.run(excel_row_parser, input=prompt)
        output = result.get_final_output()
        parsed = json.loads(output)
        if isinstance(parsed, dict):
            return parsed
    except Exception as e:
        print(f"[LLM解析失敗] {e}")

    return {}
