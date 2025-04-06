# spec_classifier.py
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

spec_classifier_agent = Agent(
    name="SpecClassifier",
    instructions="""
你是一位資深電子零件工程師，負責從磁性元件的 PDF 規格書中提取產品料號與對應的技術規格，並根據內容分類用途與產品類型。

請執行以下任務：

1. 分析下列規格書文本內容，從中找出所有包含技術參數的產品資料列
2. 對每筆資料，提取以下欄位（若無可省略）：
   - part_number
   - impedance（Ω）
   - dcr（Ω）
   - current（mA）
   - test_frequency（MHz）
   - temp_min（最低操作溫度 °C）
   - temp_max（最高操作溫度 °C）
   - size（尺寸代號）

3. 根據規格內容，請為每筆產品加上分類標籤：
   - vendor（從內容中推論）
   - category（從下列選擇最合適一項）：
     - EMI Suppression Filter
     - Common Mode Choke
     - Chip Inductor
     - RF Inductor
     - High Current Power Inductor
     - SMD Power Inductor
     - Lan Transformer
     - Transient Voltage Suppressor
     - Low Frequency Antenna
     - Balun Filter
   - application（從以下選擇）：
     - 車用（若電流超過 5000 mA 且低 DCR）
     - 一般商用

請以如下 JSON 陣列格式回傳（禁止補充說明）：
[
  {
    "part_number": "...",
    "impedance": ...,
    "dcr": ...,
    "current": ...,
    "test_frequency": ...,
    "temp_min": ...,
    "temp_max": ...,
    "size": "...",
    "vendor": "...",
    "category": "...",
    "application": "..."
  }
]
""",
    model=model
)

async def classify_specs_from_text(text: str) -> list[dict]:
    try:
        prompt = text[:12000]  # 防止超過 token 限制
        result = await Runner.run(spec_classifier_agent, prompt)
        if not result or not result.final_output:
            print("[SpecClassifier] 無回傳結果")
            return []

        match = re.search(r"\[.*\]", result.final_output, re.DOTALL)
        return json.loads(match.group(0)) if match else []

    except Exception as e:
        print(f"[SpecClassifier] 分析錯誤：{e}")
        return []
