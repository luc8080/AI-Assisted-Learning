import re
import json
from PyPDF2 import PdfReader
from pathlib import Path

def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    all_text = ""
    for page in reader.pages:
        all_text += page.extract_text() + "\n"
    return all_text

def split_into_questions(raw_text):
    # 假設題號為 1.、2. 開頭
    return re.split(r"\n\d+\. ", raw_text)[1:]  # 忽略前導內容

def parse_question_block(qtext, qnum, source="未標示試卷"):
    match = re.search(r"(.*?)(\n\([A-D]\).*)", qtext, re.DOTALL)
    if not match:
        return None

    stem = match.group(1).strip()
    choices_text = match.group(2).strip()

    choices = {}
    for opt in re.findall(r"\(([ABCD])\)([^\(\n]+)", choices_text):
        choices[opt[0]] = opt[1].strip()

    return {
        "題號": f"{source}-{qnum}",
        "題幹": stem,
        "選項": choices,
        "正解": "",  # 待補
        "出處": source,
        "類型": "單選題",
        "主題": "待分類",
        "段落標題": "待補",
        "關鍵詞": []
    }

def parse_exam_pdf_to_json(pdf_path, json_output_path, source_label="學測試題"):
    text = extract_text_from_pdf(pdf_path)
    question_blocks = split_into_questions(text)

    parsed = []
    for i, block in enumerate(question_blocks, 1):
        result = parse_question_block(block, i, source=source_label)
        if result:
            parsed.append(result)

    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)

    print(f"✅ 解析完成，共儲存 {len(parsed)} 題至 {json_output_path}")

# 範例用法：
if __name__ == "__main__":
    parse_exam_pdf_to_json(
        pdf_path="data/01-114學測國綜試題.pdf",
        json_output_path="data_store/114_國綜.json",
        source_label="114國綜"
    )
