import streamlit as st
import sqlite3
import json

DB_PATH = "data_store/question_bank.sqlite"

st.title('題庫維護管理介面')

# ----------- 工具函式 --------------
def get_questions(keyword=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if keyword:
        rows = c.execute(
            "SELECT id, passage, text, options, answer, analysis, difficulty, tags FROM questions WHERE text LIKE ? ORDER BY id DESC", ('%' + keyword + '%',)
        ).fetchall()
    else:
        rows = c.execute(
            "SELECT id, passage, text, options, answer, analysis, difficulty, tags FROM questions ORDER BY id DESC"
        ).fetchall()
    conn.close()
    return rows

def update_question(qid, field, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"UPDATE questions SET {field}=? WHERE id=?", (value, qid))
    conn.commit()
    conn.close()

def add_question(**kwargs):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO questions (passage, text, options, answer, analysis, difficulty, tags) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            kwargs.get("passage", ""),
            kwargs["text"],
            json.dumps(kwargs.get("options", [])),
            kwargs["answer"],
            kwargs.get("analysis", ""),
            kwargs.get("difficulty", ""),
            json.dumps(kwargs.get("tags", [])),
        ),
    )
    conn.commit()
    conn.close()

# ----------- Streamlit UI --------------

st.subheader("查詢題庫")
keyword = st.text_input("關鍵字查詢")
rows = get_questions(keyword)

st.write(f"共找到 {len(rows)} 筆題目")
for row in rows[:20]:  # 只顯示前20題避免一次太多
    with st.expander(f"[ID {row[0]}] {row[2][:25]}..."):
        st.write(f"**閱讀文本**：{row[1]}")
        st.write(f"**題目本體**：{row[2]}")
        st.write(f"**選項**：{json.loads(row[3]) if row[3] else []}")
        st.write(f"**答案**：{row[4]}")
        st.write(f"**解析**：{row[5]}")
        st.write(f"**難度**：{row[6]}")
        st.write(f"**標籤**：{json.loads(row[7]) if row[7] else []}")
        # 編輯區塊
        st.write("---")
        if st.checkbox("編輯這一題", key=f"edit_{row[0]}"):
            new_passage = st.text_area("閱讀文本", row[1] or "", key=f"pass_{row[0]}")
            new_text = st.text_area("題目本體", row[2], key=f"text_{row[0]}")
            new_options = st.text_area("選項(JSON Array)", row[3] or "[]", key=f"opt_{row[0]}")
            new_answer = st.text_input("答案", row[4] or "", key=f"ans_{row[0]}")
            new_analysis = st.text_area("解析", row[5] or "", key=f"ana_{row[0]}")
            new_difficulty = st.text_input("難度", row[6] or "", key=f"diff_{row[0]}")
            new_tags = st.text_area("標籤(JSON Array)", row[7] or "[]", key=f"tags_{row[0]}")
            if st.button("儲存變更", key=f"save_{row[0]}"):
                update_question(row[0], "passage", new_passage)
                update_question(row[0], "text", new_text)
                update_question(row[0], "options", new_options)
                update_question(row[0], "answer", new_answer)
                update_question(row[0], "analysis", new_analysis)
                update_question(row[0], "difficulty", new_difficulty)
                update_question(row[0], "tags", new_tags)
                st.success("已儲存！請重新查詢刷新頁面。")

st.write("---")

st.subheader("新增題目")
with st.form("add_question_form"):
    passage = st.text_area("閱讀文本")
    text = st.text_area("題目本體", required=True)
    options = st.text_area("選項(JSON Array)", "[]")
    answer = st.text_input("答案", required=True)
    analysis = st.text_area("解析")
    difficulty = st.text_input("難度")
    tags = st.text_area("標籤(JSON Array)", "[]")
    submitted = st.form_submit_button("新增題目")
    if submitted:
        try:
            add_question(
                passage=passage,
                text=text,
                options=json.loads(options),
                answer=answer,
                analysis=analysis,
                difficulty=difficulty,
                tags=json.loads(tags),
            )
            st.success("新增成功！")
        except Exception as e:
            st.error(f"新增失敗：{e}")
