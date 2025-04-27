import streamlit as st
import sqlite3
import bcrypt

def load_users():
    conn = sqlite3.connect("data_store/user_log.sqlite")
    cursor = conn.cursor()
    cursor.execute("SELECT username, password_hash, role FROM users")
    users = cursor.fetchall()
    conn.close()

    users_dict = {}
    for username, password_hash, role in users:
        users_dict[username] = {
            "password_hash": password_hash,
            "role": role
        }
    return users_dict

def run_login_view():
    st.title("🔐 登入系統")

    users = load_users()

    username_input = st.text_input("帳號")
    password_input = st.text_input("密碼", type="password")

    if st.button("登入"):
        if username_input in users:
            stored_hash = users[username_input]["password_hash"].encode('utf-8')
            if bcrypt.checkpw(password_input.encode('utf-8'), stored_hash):
                st.success(f"歡迎回來，{username_input}！")
                st.session_state.username = username_input
                st.session_state.role = users[username_input]['role']
                st.rerun()
            else:
                st.error("密碼錯誤，請再試一次！")
        else:
            st.error("查無此帳號，請確認輸入。")
