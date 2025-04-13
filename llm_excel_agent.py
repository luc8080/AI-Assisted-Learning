# === 檔案路徑：llm_excel_agent.py
# === 功能說明：
# 使用 Gemini LLM 處理每一列 Excel row，將其轉換為標準化產品規格 dict
# === 最後更新：2025-04-13

import os
import json
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

# === 建立 Agent ===
excel_agent = Agent(
    name="ExcelSpecParser",
    instructions="""
你是一位擅長處理電子零件規格表的分析助理，任務是將一筆 Excel 表格列資料（dict）轉換為標準化的磁性元件規格格式。

請根據欄位意義，自動對應並轉換為以下標準欄位：
- part_number
- impedance（阻抗，單位：Ω）
- dcr（直流電阻，單位：Ω）
- current（額定電流，單位：mA）
- test_frequency（測試頻率，單位：MHz）
- size（封裝尺寸，如 0603、1005 等）
- temp_min / temp_max（最低 / 最高溫度，單位：℃）
- category（產品分類，如 Ferrite Bead）
- application（應用領域，如 Automotive）

輸出請使用 JSON 格式，不需多餘說明，範例如下：
{
  "part_number": "HFZ1608S601T",
  "impedance": 600,
  "dcr": 0.25,
  "current": 500,
  "test_frequency": 100,
  "size": "0603",
  "temp_min": -40,
  "temp_max": 125,
  "category": "Ferrite Bead",
  "application": "Industrial"
}

請注意：
- 單位請轉換為標準單位（如：電流為 mA）
- 請避免回傳空值或未知欄位
""",
    model=model
)

# === 處理單筆 row（dict）並回傳標準欄位 ===
async def parse_spec_row_with_llm(row_dict: dict) -> dict:
    prompt = f"請將以下 Excel 資料轉為標準化產品規格 JSON：\n{json.dumps(row_dict, ensure_ascii=False)}"
    runner = Runner(agents=[excel_agent], model=model)
    result = await runner.run(input=prompt)

    try:
        content = result.final_output if hasattr(result, "final_output") else getattr(result, "get_final_output", lambda: "")()
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else {}
    except Exception as e:
        print(f"[LLM 解析失敗] {e}")
        return {}
