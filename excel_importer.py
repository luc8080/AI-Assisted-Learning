# === 檔案路徑：excel_importer.py
# === 功能說明：
# 匯入 Excel 或資料夾內 Excel 檔案，透過 LLM 或欄位對應轉為結構化資料存入資料庫
# 支援依產品分類補足必要欄位
# === 最後更新：2025-04-13

import os
import json
import pandas as pd
import asyncio
from database import save_structured_spec_to_db
from dotenv import load_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel

# === 初始化 LLM 模型 ===
load_dotenv()
client = AsyncOpenAI(
    base_url=os.getenv("GOOGLE_GEMINI_ENDPOINT"),
    api_key=os.getenv("GOOGLE_GEMINI_API_KEY")
)
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

# === LLM 規格解析 Agent ===
parser_agent = Agent(
    name="ExcelRowParser",
    instructions="""
你是一位專業的電子零件規格判讀助手。請根據 Excel 表格中的欄位與資料，
嘗試推論每個欄位代表的標準磁性元件規格，轉為以下結構：

- part_number
- impedance
- dcr
- current
- test_frequency
- temp_min
- temp_max
- size
- category
- application
- material
- packaging
- tolerance
- rated_voltage

請直接回傳 JSON 格式，忽略無關欄位。
""",
    model=model
)

CATEGORY_REQUIRED_FIELDS = {
    "Ferrite Bead": ["part_number", "impedance", "dcr", "current", "size"],
    "Chip Inductor": ["part_number", "inductance", "dcr", "current", "size"],
    "Common Mode Filter": ["part_number", "impedance", "current", "test_frequency", "size"]
}

async def parse_spec_row_with_llm(row: dict) -> dict:
    prompt = f"請協助將以下資料列轉為標準規格欄位：\n{json.dumps(row, ensure_ascii=False)}"
    runner = Runner(agents=[parser_agent])
    result = await runner.run(input=prompt)

    try:
        output = result.get_final_output()
        parsed = json.loads(output)
        return parsed if isinstance(parsed, dict) else {}
    except Exception as e:
        print(f"[LLM 解析失敗] {e}")
        return {}

# === 靜態欄位對應表 ===
STATIC_FIELD_MAP = {
    "Part Number": "part_number",
    "Tai-Tech Part Number": "part_number",
    "Impedance (Ω)": "impedance",
    "Impedance (Ohm)": "impedance",
    "DC Resistance (Ω) max.": "dcr",
    "Rated Current (mA) max.": "current",
    "Rated Current": "current",
    "Test Frequency (MHz)": "test_frequency",
    "Chip Size": "size",
    "尺寸": "size",
    "Material": "material",
    "Packaging": "packaging",
    "Tolerance": "tolerance",
    "Rated Voltage": "rated_voltage",
    "Operating Temperature": "temp_range"
}

# === 靜態 fallback 欄位轉換 ===
def convert_with_static_mapping(row_dict: dict) -> dict:
    result = {}
    for key, value in row_dict.items():
        mapped_key = STATIC_FIELD_MAP.get(key)
        if mapped_key:
            result[mapped_key] = value

    if "temp_range" in result and isinstance(result["temp_range"], str):
        parts = result["temp_range"].replace("℃", "").split("~")
        if len(parts) == 2:
            try:
                result["temp_min"] = float(parts[0])
                result["temp_max"] = float(parts[1])
            except:
                pass
    return result

# === 補齊必要欄位 ===
def fill_required_fields(parsed: dict):
    category = parsed.get("category", "Ferrite Bead")
    required_fields = CATEGORY_REQUIRED_FIELDS.get(category, [])
    for field in required_fields:
        if field not in parsed:
            parsed[field] = None
    return parsed

# === 匯入單一 Excel 檔案 ===
async def import_excel_file(filepath: str, vendor: str = "Tai-Tech", use_llm: bool = True):
    df = pd.read_excel(filepath, engine="openpyxl")
    filename = os.path.basename(filepath)
    application = infer_application(filename)
    structured_rows = []

    for _, row in df.iterrows():
        try:
            parsed = await parse_spec_row_with_llm(row.to_dict()) if use_llm else convert_with_static_mapping(row.to_dict())
            if isinstance(parsed, dict) and parsed.get("part_number"):
                parsed["vendor"] = vendor
                parsed["application"] = parsed.get("application") or application
                parsed["category"] = parsed.get("category") or "Ferrite Bead"
                parsed = fill_required_fields(parsed)
                save_structured_spec_to_db(parsed, vendor, filename)
                structured_rows.append(parsed)
        except Exception as e:
            print(f"❌ 匯入失敗 {filename}：{e}")

    print(f"✅ 完成 {filename} 匯入，共 {len(structured_rows)} 筆")

# === 匯入資料夾中所有 Excel 檔案 ===
async def import_excel_folder(folder_path: str, vendor: str = "Tai-Tech", use_llm: bool = True):
    count = 0
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".xlsx") or file.endswith(".xls"):
                full_path = os.path.join(root, file)
                print(f"📥 匯入：{full_path}")
                await import_excel_file(full_path, vendor=vendor, use_llm=use_llm)
                count += 1
    print(f"📦 共匯入 {count} 份 Excel 檔案")

# === 檔名推論應用場景 ===
def infer_application(filename: str) -> str:
    if "車用" in filename:
        return "Automotive"
    elif "工控" in filename:
        return "Industrial"
    elif "通訊" in filename:
        return "Communication"
    return "General"
