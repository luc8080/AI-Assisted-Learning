import sqlite3
import random
import json

DB_PATH = "data_store/question_bank.sqlite"

# === 取得所有單題 ===
def get_all_single_questions():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, content, options, answer, explanation, topic, difficulty, question_type
        FROM questions
        WHERE group_id IS NULL
    """)
    results = c.fetchall()
    conn.close()
    questions = []
    for row in results:
        questions.append({
            "type": "single",
            "題號": row[0],
            "題幹": row[1],
            "選項": json.loads(row[2]) if row[2] else {},
            "正解": row[3],
            "解析": row[4],
            "主題": row[5],
            "難度": row[6],
            "題型": row[7],
        })
    return questions

# === 取得所有題組 ===
def get_all_question_groups():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, title, reading_text, category
        FROM question_groups
    """)
    groups = c.fetchall()
    result = []
    for group_row in groups:
        group_id, title, reading_text, category = group_row
        c.execute("""
            SELECT id, content, options, answer, explanation, topic, difficulty, question_type
            FROM questions
            WHERE group_id = ?
        """, (group_id,))
        subquestions = []
        for q in c.fetchall():
            subquestions.append({
                "sub_id": q[0],
                "題幹": q[1],
                "選項": json.loads(q[2]) if q[2] else {},
                "正解": q[3],
                "解析": q[4],
                "主題": q[5],
                "難度": q[6],
                "題型": q[7],
            })
        result.append({
            "type": "group",
            "group_id": group_id,
            "title": title,
            "reading_text": reading_text,
            "category": category,
            "questions": subquestions
        })
    conn.close()
    return result

# === 取得隨機單題或題組（可帶模式）===
def get_random_question(mode="auto"):
    singles = get_all_single_questions()
    groups = get_all_question_groups()
    all_items = singles + groups

    if not all_items:
        return None

    # auto: 單題與題組皆可隨機抽
    item = random.choice(all_items)
    return item

def get_random_single_question():
    singles = get_all_single_questions()
    if not singles:
        return None
    return random.choice(singles)

def get_random_group():
    groups = get_all_question_groups()
    if not groups:
        return None
    return random.choice(groups)

# === 依據題號/小題 id 查單題或題組小題 ===
def get_question_by_id(qid):
    """
    輸入題號（單題為 id，題組小題為 sub_id），自動判斷來源
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # 先查單題
    c.execute("""
        SELECT id, content, options, answer, explanation, topic, difficulty, question_type
        FROM questions
        WHERE id = ? AND group_id IS NULL
    """, (qid,))
    row = c.fetchone()
    if row:
        conn.close()
        return {
            "type": "single",
            "題號": row[0],
            "題幹": row[1],
            "選項": json.loads(row[2]) if row[2] else {},
            "正解": row[3],
            "解析": row[4],
            "主題": row[5],
            "難度": row[6],
            "題型": row[7],
        }
    # 查題組內小題
    c.execute("""
        SELECT q.id, q.content, q.options, q.answer, q.explanation, q.topic, q.difficulty, q.question_type,
               g.id, g.title, g.reading_text, g.category
        FROM questions q
        JOIN question_groups g ON q.group_id = g.id
        WHERE q.id = ?
    """, (qid,))
    row = c.fetchone()
    if row:
        conn.close()
        return {
            "type": "group_sub",
            "sub_id": row[0],
            "題幹": row[1],
            "選項": json.loads(row[2]) if row[2] else {},
            "正解": row[3],
            "解析": row[4],
            "主題": row[5],
            "難度": row[6],
            "題型": row[7],
            "group_id": row[8],
            "group_title": row[9],
            "reading_text": row[10],
            "category": row[11]
        }
    conn.close()
    return None
