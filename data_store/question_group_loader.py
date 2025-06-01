# 檔案路徑：learning_assistant/data_store/question_group_loader.py

import sqlite3
import json
import os

DB_PATH = "data_store/question_bank.sqlite"

def get_all_groups():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, reading_text, category FROM question_groups")
    groups = c.fetchall()
    result = []
    for gid, title, reading_text, category in groups:
        c.execute("SELECT id, content, options, answer, explanation, topic, difficulty, question_type FROM questions WHERE group_id=?", (gid,))
        questions = c.fetchall()
        question_list = [
            {
                "id": qid,
                "content": content,
                "選項": json.loads(options) if options else {},
                "answer": answer,
                "正解": answer,   # <--- 統一補這一行，保證每題一定有「正解」key
                "explanation": explanation,
                "topic": topic,
                "difficulty": difficulty,
                "question_type": question_type
            }
            for qid, content, options, answer, explanation, topic, difficulty, question_type in questions
        ]
        result.append({
            "group_id": gid,
            "title": title,
            "reading_text": reading_text,
            "category": category,
            "questions": question_list
        })
    conn.close()
    return result

def get_all_single_questions():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, content, options, answer, explanation, topic, difficulty, question_type FROM questions WHERE group_id IS NULL")
    singles = c.fetchall()
    result = [
        {
            "id": qid,
            "content": content,
            "選項": json.loads(options) if options else {},
            "answer": answer,
            "正解": answer,   # <--- 同理補這一行
            "explanation": explanation,
            "topic": topic,
            "difficulty": difficulty,
            "question_type": question_type
        }
        for qid, content, options, answer, explanation, topic, difficulty, question_type in singles
    ]
    conn.close()
    return result

# 批量匯入：傳入 JSON 結構（見最佳實作建議）
def import_from_json(json_data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for item in json_data:
        if 'group' in item and 'questions' in item:
            group = item['group']
            c.execute('INSERT INTO question_groups (title, reading_text, category) VALUES (?, ?, ?)',
                      (group.get('title'), group.get('reading_text'), group.get('category')))
            group_id = c.lastrowid
            for q in item['questions']:
                # 儲存 options（選項）為 JSON 字串
                options_json = json.dumps(q.get('選項') or q.get('options') or {})
                # 儲存正解（answer/正解都支援）
                answer_value = q.get('answer') or q.get('正解')
                c.execute('''INSERT INTO questions (
                                 group_id, content, options, answer, explanation, topic, difficulty, question_type
                             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                          (group_id, q['content'], options_json, answer_value,
                           q.get('explanation'), q.get('topic'),
                           q.get('difficulty', 1), q.get('question_type', '單選')))
        else:
            # 單題
            options_json = json.dumps(item.get('選項') or item.get('options') or {})
            answer_value = item.get('answer') or item.get('正解')
            c.execute('''INSERT INTO questions (
                             content, options, answer, explanation, topic, difficulty, question_type
                         ) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (item['content'], options_json, answer_value,
                       item.get('explanation'), item.get('topic'),
                       item.get('difficulty', 1), item.get('question_type', '單選')))
    conn.commit()
    conn.close()
    return "匯入成功"
