import streamlit as st
from data_store.question_group_loader import get_all_groups, import_from_json
from assistant_core.llm_generate_questions import generate_questions_with_llm
import json

def render_options(options):
    if not isinstance(options, dict) or not options:
        return "（無選項資料）"
    return "\n".join([f"({k}) {v}" for k, v in options.items()])

def run_question_bank_maintain_view():
    st.title("題庫維護（人工/AI生成/批次匯入）")

    tab1, tab2 = st.tabs(["題組管理", "批次匯入"])

    # ========== 題組管理 ========== #
    with tab1:
        # 顯示既有題組
        groups = get_all_groups()
        st.subheader(f"題組總覽（{len(groups)} 組）")
        for group in groups:
            with st.expander(f"[{group['group_id']}] {group['title']}"):
                st.markdown(f"**主題/分類：** {group.get('category', '')}")
                st.markdown(f"**閱讀文本：**\n{group['reading_text']}")
                for idx, q in enumerate(group["questions"]):
                    st.markdown(f"**小題{idx+1}：** {q.get('content', q.get('題幹', ''))}")
                    st.markdown(f"選項：\n{render_options(q.get('選項', {}))}")
                    st.markdown(f"正解：{q.get('正解', '')}")
                    st.markdown("---")

        st.divider()
        st.header("➕ 新增題組")

        # 新增題組欄位
        new_group_title = st.text_input("題組標題")
        new_group_reading = st.text_area("閱讀文本")
        new_group_category = st.text_input("主題/分類")
        # 建立小題暫存
        if "draft_questions" not in st.session_state:
            st.session_state["draft_questions"] = []
        if "ai_raw_output" not in st.session_state:
            st.session_state["ai_raw_output"] = None

        st.subheader("手動新增小題")
        with st.form("manual_add_q_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                q_stem = st.text_area("題幹")
                q_opt_a = st.text_input("選項A")
                q_opt_b = st.text_input("選項B")
            with col2:
                q_opt_c = st.text_input("選項C")
                q_opt_d = st.text_input("選項D")
                q_ans = st.selectbox("正解", ["A", "B", "C", "D"])
            add_q_btn = st.form_submit_button("加入小題")
        if add_q_btn and q_stem:
            st.session_state["draft_questions"].append({
                "題幹": q_stem,
                "選項": {"A": q_opt_a, "B": q_opt_b, "C": q_opt_c, "D": q_opt_d},
                "正解": q_ans
            })
            st.success("小題已暫存，稍後可一併存入！")

        # 顯示目前暫存小題
        if st.session_state["draft_questions"]:
            st.markdown("**已暫存小題：**")
            for i, q in enumerate(st.session_state["draft_questions"]):
                st.markdown(f"{i+1}. {q.get('content', q.get('題幹', ''))} ({q.get('正解', '')})")
                st.markdown(render_options(q.get('選項', {})))
            if st.button("清空暫存小題"):
                st.session_state["draft_questions"] = []

        st.divider()
        st.subheader("🪄 AI 生成小題 (Gemini)")

        with st.form("ai_add_q_form"):
            ai_num = st.number_input("產生題數", min_value=1, max_value=10, value=3)
            ai_btn = st.form_submit_button("用AI產生小題")
        if ai_btn and new_group_reading:
            with st.spinner("Gemini LLM 正在產生題目...（依API流量約需10秒）"):
                ai_questions, ai_raw_output = generate_questions_with_llm(new_group_reading, int(ai_num))
                # 將原始 LLM 回傳記錄下來，便於人工 debug
                st.session_state["ai_raw_output"] = ai_raw_output
                if isinstance(ai_questions, list):
                    for aiq in ai_questions:
                        st.session_state["draft_questions"].append(aiq)
                    st.success(f"已產生{len(ai_questions)}題，已暫存於下方，可人工檢查再存入！")
                else:
                    st.error("LLM 回傳非標準 list 結構，請參考下方原始回傳內容")

        # --- 顯示 AI 原始回傳 ---
        if st.session_state.get("ai_raw_output"):
            with st.expander("點此展開檢視 AI 原始回傳內容（可人工複製修正）", expanded=False):
                st.code(st.session_state["ai_raw_output"], language="text")

        # -------- 儲存時自動欄位轉換/補齊 --------
        if st.session_state["draft_questions"] and new_group_reading:
            if st.button("✅ 儲存為新題組"):
                # 將所有小題「題幹」欄位轉為 content，並補齊欄位
                formatted_questions = []
                for q in st.session_state["draft_questions"]:
                    new_q = dict(q)
                    # 統一題幹欄位
                    if "題幹" in new_q:
                        new_q["content"] = new_q.pop("題幹")
                    # 補齊選項
                    if "選項" not in new_q or not isinstance(new_q["選項"], dict):
                        new_q["選項"] = {"A": "", "B": "", "C": "", "D": ""}
                    # 補齊正解
                    if "正解" not in new_q:
                        new_q["正解"] = "A"
                    formatted_questions.append(new_q)
                import_from_json([{
                    "group": {
                        "title": new_group_title,
                        "reading_text": new_group_reading,
                        "category": new_group_category
                    },
                    "questions": formatted_questions
                }])
                st.success("題組已存入資料庫！")
                st.session_state["draft_questions"] = []
                st.session_state["ai_raw_output"] = None
                st.rerun()

    # ========== 批次匯入 ========== #
    with tab2:
        st.markdown("請貼上題組/單題 JSON 格式（同一組可混合多組題組）")
        json_text = st.text_area("JSON 輸入區")
        if st.button("批量匯入"):
            try:
                json_data = json.loads(json_text)
                msg = import_from_json(json_data)
                st.success(str(msg))
            except Exception as e:
                st.error(f"JSON 格式有誤：{e}")
        st.markdown("""
        **範例格式：**

        ```json
        [
          {
            "group": {
              "title": "閱讀理解題組1",
              "reading_text": "下列是一段關於水資源管理的短文 ...",
              "category": "閱讀理解"
            },
            "questions": [
              {
                "題幹": "根據本文，下列何者正確？",
                "選項": {"A": "...", "B": "...", "C": "...", "D": "..."},
                "正解": "B"
              }
            ]
          }
        ]
        ```
        """)

# 若直接執行測試
if __name__ == "__main__":
    run_question_bank_maintain_view()
