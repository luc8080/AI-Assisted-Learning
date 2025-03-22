import sqlite3

DB_PATH = "product_specs.db"

def init_db():
    """初始化 SQLite 資料庫"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS product_specs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        content TEXT NOT NULL)''')
    conn.commit()
    conn.close()

def save_pdf_text_to_db(text):
    """儲存解析後的 PDF 內容至資料庫"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO product_specs (content) VALUES (?)", (text,))
    conn.commit()
    conn.close()

def get_all_product_specs():
    """從資料庫擷取所有產品規格"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM product_specs")
    rows = cursor.fetchall()
    conn.close()
    return "\n".join([row[0] for row in rows]) if rows else None
