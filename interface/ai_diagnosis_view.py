# 檔案路徑：interface/ai_diagnosis_view.py

import streamlit as st
import sqlite3
import pandas as pd
import asyncio
import json
from agents import Runner
from assistant_core.ai_diagnosis_agent import ai_diagnosis_agent

LOG_DB_PATH = "data_store/user_log.sqlite"
QBANK_DB_PATH = "data_store/question_bank.sqlite"

def get_recent_wrong_questions(username, limit=5):
    conn = sqlite3.connect(LOG_DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    if not row:
        return []
    user_id = row[0]
    df = pd.read_sql_query("""
        SELECT question_id, student_answer, correct_answer, MAX(timestamp) as last_ts
        FROM answer_log
        WHERE user_id = ? AND is_correct = 0
        GROUP BY question_id
        ORDER BY last_ts DESC
        LIMIT ?
    """, conn, params=(user_id, limit))
    conn.close()
    return df.to_dict(orient="records")

def get_question_detail(qid):
    conn = sqlite3.connect(QBANK_DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT q.id, q.content, q.options, q.answer, q.explanation, q.topic, q.keywords, g.reading_text, g.title, g.category
        FROM questions q
        LEFT JOIN question_groups g ON q.group_id = g.id
        WHERE q.id = ?
    """, (qid,))
    row = c.fetchone()
    conn.close()
    if not row:
        return {}
    options = {}
    try:
        options = json.loads(row[2]) if row[2] else {}
    except Exception:
        options = {}
    return {
        "題號": row[0],
        "題幹": row[1],
        "選項": options,
        "正解": row[3],
        "解析": row[4],
        "主題": row[5],
        "關鍵詞": row[6],
        "閱讀文本": row[7],
        "題組標題": row[8],
        "分類": row[9]
    }

def run_ai_diagnosis_view():
    st.title("AI 智能診斷與個人化建議")

    username = st.session_state.get('username', None)
    if not username:
        st.warning("請先登入")
        return

    # 取得最近錯題
    wrong_list = get_recent_wrong_questions(username)
    if not wrong_list:
        st.info("目前沒有可診斷的錯題。")
        return

    options = [f"題號 {w['question_id']}（你的答案:{w['student_answer']}/正解:{w['correct_answer']}）" for w in wrong_list]
    choice = st.selectbox("請選擇要診斷的錯題", options, index=0)
    qinfo = wrong_list[options.index(choice)]
    q_detail = get_question_detail(qinfo['question_id'])

    st.markdown(f"**題目：** {q_detail.get('題幹','')}")
    if q_detail.get("閱讀文本"):
        with st.expander("（點此展開閱讀文本）"):
            st.markdown(q_detail["閱讀文本"])
    st.markdown("**選項：**")
    for k, v in q_detail.get("選項", {}).items():
        st.markdown(f"({k}) {v}")
    st.markdown(f"**你的答案：** {qinfo['student_answer']}  \n**正確答案：** {qinfo['correct_answer']}")
    st.markdown(f"**主題：** {q_detail.get('主題','未分類')}")
    st.markdown(f"**關鍵詞：** {q_detail.get('關鍵詞','無')}")
    st.markdown(f"**所屬題組：** {q_detail.get('題組標題','') or '（單題）'} / 分類：{q_detail.get('分類','')}")

    if st.button("產生 AI 智能診斷與回饋"):
        prompt = {
            "題號": q_detail.get('題號'),
            "閱讀文本": q_detail.get('閱讀文本'),
            "題幹": q_detail.get('題幹'),
            "選項": q_detail.get('選項'),
            "學生答案": qinfo['student_answer'],
            "正確答案": qinfo['correct_answer'],
            "主題": q_detail.get('主題'),
            "關鍵詞": q_detail.get('關鍵詞'),
            "解析": q_detail.get('解析'),
            "題組標題": q_detail.get('題組標題'),
            "分類": q_detail.get('分類')
        }
        st.info("AI 診斷中，請稍候...")
        ai_prompt = json.dumps(prompt, ensure_ascii=False, indent=2)
        try:
            result = asyncio.run(Runner.run(ai_diagnosis_agent, input=ai_prompt))
            st.success("AI 診斷完成：")
            st.markdown(result.final_output)
        except Exception as e:
            st.error(f"AI 分析失敗：{e}")

# main.py 或側邊欄選單入口
if __name__ == "__main__":
    run_ai_diagnosis_view()
