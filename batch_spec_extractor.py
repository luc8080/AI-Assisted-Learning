# batch_spec_extractor.py
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
    model="gemini-2.0-flash",
    openai_client=client
)

batch_extractor_agent = Agent(
    name="BatchSpecExtractor",
    instructions="""
你是一位鐵氧體磁珠產品工程師。你收到一整份產品規格書的文字內容，請協助從中找出所有產品的料號與對應規格，並輸出為 JSON 陣列。

請根據下列格式輸出：

[
  {
    "part_number": "HFZ3216-601T",
    "impedance": 數值（Ω）,
    "test_frequency": 數值（MHz）,
    "dcr": 數值（Ω）,
    "current": 數值（mA）,
    "temp_min": 數值（°C）,
    "temp_max": 數值（°C）,
    "size": "3216"
  },
  ...
]

若資料不足可略過欄位，禁止補充說明。僅回傳純 JSON 陣列。
""",
    model=model
)

async def extract_multiple_specs_from_text(text: str) -> list[dict]:
    try:
        prompt = text[:12000]  # 避免超出 token 限制
        result = await Runner.run(batch_extractor_agent, prompt)
        if not result or not result.final_output:
            print("[BatchExtractor] ⚠️ 沒有回傳結果")
            return []

        match = re.search(r"\[.*\]", result.final_output, re.DOTALL)
        return json.loads(match.group(0)) if match else []

    except Exception as e:
        print(f"[BatchExtractor] 錯誤：{e}")
        return []
