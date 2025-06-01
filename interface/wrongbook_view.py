# 檔案路徑：interface/wrongbook_view.py

import streamlit as st
import sqlite3
from data_store.question_loader import get_question_by_id
import pandas as pd
from collections import Counter
import datetime

LOG_DB_PATH = "data_store/user_log.sqlite"
QUESTION_DB_PATH = "data_store/question_bank.sqlite"

def get_user_id(username):
    conn = sqlite3.connect(LOG_DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    user_row = c.fetchone()
    conn.close()
    return user_row[0] if user_row else None

def get_wrong_log(user_id):
    conn = sqlite3.connect(LOG_DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT question_id, group_id, sub_id, student_answer, correct_answer, MAX(timestamp)
        FROM answer_log
        WHERE user_id = ? AND is_correct = 0
        GROUP BY question_id, group_id, sub_id
        ORDER BY MAX(timestamp) DESC
    """, (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_question_topic(qid):
    conn = sqlite3.connect(QUESTION_DB_PATH)
    c = conn.cursor()
    c.execute("SELECT topic, keywords FROM questions WHERE id = ?", (qid,))
    row = c.fetchone()
    conn.close()
    return (row[0], row[1]) if row else ("未分類", "")

def get_all_wrong_topics(wrong_logs):
    topics = []
    keywords = []
    for row in wrong_logs:
        qid = row[0]
        topic, kws = get_question_topic(qid)
        if topic: topics.append(topic)
        if kws: keywords += [k.strip() for k in kws.split(",") if k.strip()]
    return topics, keywords

def summarize_error_patterns(wrong_logs):
    # 以簡單規則產生摘要
    if not wrong_logs:
        return ""
    last_5 = wrong_logs[:5]
    topic_count = Counter([get_question_topic(row[0])[0] for row in last_5])
    if topic_count:
        top_topic = topic_count.most_common(1)[0][0]
        return f"你最近的錯題多屬於「{top_topic}」類型，建議加強該主題練習。"
    return "近期錯題分散，建議多回顧解析並練習易錯類型。"

def get_weekly_review_recommendation(wrong_logs):
    # 推薦本週回顧題號
    week_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()
    week_ids = []
    for row in wrong_logs:
        if row[-1] > week_ago:
            week_ids.append(row[0])
    if week_ids:
        return f"本週推薦回顧題目：{', '.join([str(i) for i in week_ids[:5]])}"
    return "本週沒有新錯題，建議複習舊錯題。"

def render_options(options, my_ans=None, correct_ans=None):
    res = []
    for k, v in options.items():
        label = f"({k}) {v}"
        if my_ans == k:
            label += "  ⬅️ 你的答案"
        if correct_ans == k:
            label += "  ✅ 正解"
        res.append(label)
    return "\n".join(res)

def run_wrongbook_view():
    st.header("我的錯題本（AI 整理回顧）")
    username = st.session_state.get('username', None)
    if not username:
        st.error("請先登入")
        return

    user_id = get_user_id(username)
    if not user_id:
        st.error("查無此帳號")
        return

    wrong_logs = get_wrong_log(user_id)
    if not wrong_logs:
        st.info("目前沒有錯題紀錄，請繼續努力學習！")
        return

    # === AI 高頻錯因摘要 ===
    st.subheader("AI 錯題重點提醒")
    st.info(summarize_error_patterns(wrong_logs))

    # === 主題分類統計圖 ===
    topics, keywords = get_all_wrong_topics(wrong_logs)
    if topics:
        topic_count = Counter(topics)
        df_topic = pd.DataFrame(topic_count.items(), columns=["主題", "錯題數"])
        st.bar_chart(df_topic.set_index("主題"))
    if keywords:
        kw_count = Counter(keywords)
        st.markdown("**高頻關鍵詞：** " + "、".join([k for k, v in kw_count.most_common(10)]))

    # === 本週回顧推薦 ===
    st.subheader("本週錯題回顧推薦")
    st.warning(get_weekly_review_recommendation(wrong_logs))

    # === 分組顯示所有錯題 ===
    st.subheader("我的錯題列表")
    for row in wrong_logs:
        qid, group_id, sub_id, my_ans, correct_ans, last_ts = row
        q = get_question_by_id(qid)
        if not q:
            continue

        qid_disp = q.get('題號') or q.get('sub_id') or q.get('id')
        topic, kws = get_question_topic(qid)
        expander_label = f"【{topic}】題號：{qid_disp} | 最近作答：{last_ts}"
        with st.expander(expander_label):
            # 主題/關鍵詞標籤
            if kws:
                st.caption(f"關鍵詞：{kws}")

            # 閱讀素材/題目/選項
            if q.get("type") in ("group_sub",):
                st.markdown(f"**閱讀文本：**\n{q.get('reading_text', '')}")
            st.markdown(f"**題目：** {q.get('題幹', '')}")
            st.markdown(f"**選項：**\n{render_options(q.get('選項', {}), my_ans, correct_ans)}")
            st.markdown(f"**我的答案：** {my_ans}")
            st.markdown(f"**正解：** {correct_ans}")

            # 標準解析
            explanation = q.get("解析") or q.get("explanation")
            showexp = st.checkbox("顯示解析", key=f"showexp_{qid_disp}")
            if explanation and explanation.strip() and showexp:
                st.markdown(explanation)

            # 「一鍵進階 AI」按鈕（但主頁只給標準解析）
            if st.button("進階 AI 教練對話", key=f"coach_{qid_disp}"):
                st.session_state["coach_entry_qid"] = qid
                st.info("請切換至『AI 教練互動』功能頁進行對話！")

            if st.button("進階 AI 智能診斷", key=f"diag_{qid_disp}"):
                st.session_state["diagnosis_entry_qid"] = qid
                st.info("請切換至『AI 智能診斷』功能頁進行診斷！")

