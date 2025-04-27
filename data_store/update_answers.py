import sqlite3
import json
from pathlib import Path

def update_answers_from_json(json_path, sqlite_path="data_store/question_bank.sqlite"):
    if not Path(json_path).exists():
        raise FileNotFoundError(f"找不到 JSON 檔案：{json_path}")
    if not Path(sqlite_path).exists():
        raise FileNotFoundError(f"找不到 SQLite 資料庫：{sqlite_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        answer_dict = json.load(f)

    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()

    updated = 0
    for num_str, answer in answer_dict.items():
        try:
            qnum = int(num_str)
            qid = f"114國綜-{qnum}"
            cursor.execute("UPDATE questions SET answer = ? WHERE id = ?", (answer, qid))
            updated += cursor.rowcount
        except Exception as e:
            print(f"❗ 無法更新題號 {num_str}: {e}")

    conn.commit()
    conn.close()
    print(f"✅ 已成功更新 {updated} 題的正確答案。")

# 範例用法：
if __name__ == "__main__":
    update_answers_from_json("data_store/114_國綜_正解.json")
