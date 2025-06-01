import os
import json
import re
from dotenv import load_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
import asyncio

# === 初始化 Gemini 模型 ===
load_dotenv()
api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
endpoint = os.getenv("GOOGLE_GEMINI_ENDPOINT")

if not api_key or not endpoint:
    raise ValueError("❌ 請設定 GOOGLE_GEMINI_API_KEY 與 GOOGLE_GEMINI_ENDPOINT 環境變數")

client = AsyncOpenAI(
    base_url=endpoint,
    api_key=api_key
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

# === AI 產題 Agent ===
question_gen_agent = Agent(
    name="QuestionGenerationAgent",
    instructions="""
你是一位資深國文老師，請根據給定閱讀文本，產生指定數量的素養導向單選題，每題格式必須為：
{"題幹": "...", "選項": {"A":"...", "B":"...", "C":"...", "D":"..."}, "正解":"A"}
每一題「必須同時」包含「題幹」、「選項」、「正解」三個欄位，且選項必須有A、B、C、D四個選項。
請以純 JSON list 輸出，每題一個 dict，**禁止加上```json或```標記**，不得省略任何欄位。
""",
    model=model
)

def extract_json_from_llm_output(output):
    """
    處理 LLM 回傳如 ```json ... ``` 或 ``` ... ``` 的情形，只抽出中間 JSON
    """
    output = output.strip()
    if output.startswith("```"):
        output = re.sub(r"^```[a-zA-Z]*\n?", "", output)
        output = re.sub(r"\n?```$", "", output)
    return output.strip()

def generate_questions_with_llm(reading_text, num_questions=5):
    """
    用 Gemini LLM 產生素養導向小題（同步呼叫，適用 Streamlit）
    回傳: (questions_list, llm_raw_output)
    """
    prompt = f"""
請根據以下閱讀文本，產生 {num_questions} 題素養導向單選題，附標準答案。
閱讀文本：
{reading_text}

輸出範例（務必為純 JSON list，不得加```json或```標記）：
[
  {{"題幹": "下列哪一敘述最符合本文？", "選項": {{"A":"...","B":"...","C":"...","D":"..."}}, "正解":"B"}},
  ...
]
"""
    try:
        result = asyncio.run(Runner.run(question_gen_agent, input=prompt))
        output = result.final_output
        output_json = extract_json_from_llm_output(output)
        questions = json.loads(output_json)
        if isinstance(questions, list):
            # 防呆：自動補齊選項與正解欄位
            for q in questions:
                if "選項" not in q or not isinstance(q["選項"], dict):
                    q["選項"] = {"A": "（AI未產生）", "B": "（AI未產生）", "C": "（AI未產生）", "D": "（AI未產生）"}
                else:
                    for key in ["A", "B", "C", "D"]:
                        if key not in q["選項"]:
                            q["選項"][key] = "（AI未產生）"
                if "正解" not in q:
                    q["正解"] = "A"
            return questions, output  # << 回傳兩個
        else:
            return [{"題幹": "LLM格式錯誤: 並非list", "選項": {"A": "N/A"}, "正解": "A"}], output
    except Exception as e:
        # 如果 parse 失敗，回傳原始 output
        return [{"題幹": f"無法解析LLM內容: {e}", "選項": {"A": "N/A"}, "正解": "A"}], locals().get("output", "")

