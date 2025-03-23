# spec_extractor.py
import os
import json
import re
from dotenv import load_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel

load_dotenv()

client = AsyncOpenAI(
    base_url=os.getenv("GOOGLE_GEMINI_ENDPOINT"),
    api_key=os.getenv("GOOGLE_GEMINI_API_KEY")
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-pro",  # 使用較強模型以利表格理解
    openai_client=client
)

extractor_agent = Agent(
    name="SpecExtractor",
    instructions="""
你是一位鐵氧體磁珠產品工程師，專門將產品表格資訊轉換為 JSON 格式規格參數。
請勿補充解釋，僅回傳 JSON。
""",
    model=model
)

# 可補欄位對應
FALLBACK_FIELD_MAP = {
    "part_number": ["part_number"],
    "impedance": ["impedance"],
    "dcr": ["dcr", "dc resistance"],
    "current": ["current", "rated current"],
    "test_frequency": ["test_frequency"],
    "temp_min": ["temp_min", "low temp", "min temp"],
    "temp_max": ["temp_max", "high temp", "max temp"],
    "size": ["size"]
}

def fallback_fill_fields(result_dict: dict, original_row: dict) -> dict:
    result = result_dict.copy()
    for field, possible_keys in FALLBACK_FIELD_MAP.items():
        if field in result:
            continue
        for k in original_row:
            if not k or not isinstance(k, str):
                continue
            key_lower = k.strip().lower()
            if any(alias in key_lower for alias in possible_keys):
                val = original_row.get(k)
                if val and isinstance(val, str) and val.strip():
                    result[field] = val.strip()
                    break
    return result

async def extract_spec_dict_from_text(part_number: str, raw: str | dict) -> dict:
    try:
        input_block = json.dumps(raw, ensure_ascii=False) if isinstance(raw, dict) else raw

        prompt = f"""
你是一位鐵氧體磁珠產品工程師，請從下列產品表格資料中擷取產品規格，並回傳 JSON 格式，僅回傳 JSON，不要加任何說明。

表格資料如下：
{input_block}

請輸出以下格式（依實際資料填入，欄位可略過）：

{{
  "part_number": "...",
  "impedance": 數值（Ω）,
  "test_frequency": 數值（MHz）,
  "dcr": 數值（Ω）,
  "current": 數值（mA）,
  "temp_min": 溫度（°C）,
  "temp_max": 溫度（°C）,
  "size": "3216"
}}

只要 JSON 結構，禁止補充說明。資料無法得知可省略。
"""

        result = await Runner.run(extractor_agent, prompt)
        text = result.final_output

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            print(f"[SpecExtractor] ⚠️ LLM 未回傳 JSON：\n{text}")
            return {}

        parsed = json.loads(match.group(0))
        parsed.setdefault("part_number", part_number)

        if isinstance(raw, dict):
            parsed = fallback_fill_fields(parsed, raw)

        return parsed

    except Exception as e:
        print(f"[SpecExtractor] 錯誤：{e}")
        return {}
