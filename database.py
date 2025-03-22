import sqlite3

db_path = "product_specs.db"

def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS product_specs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        content TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS query_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_input TEXT NOT NULL,
                        response TEXT NOT NULL)''')
    conn.commit()
    conn.close()

def save_pdf_text_to_db(text):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO product_specs (content) VALUES (?)", (text,))
    conn.commit()
    conn.close()

def check_database_status():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM product_specs")
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def save_query_to_db(user_input, response):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO query_history (user_input, response) VALUES (?, ?)", (user_input, response))
    conn.commit()
    conn.close()

def get_all_queries():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT user_input, response FROM query_history")
    rows = cursor.fetchall()
    conn.close()
    return rows