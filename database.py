# database.py
import sqlite3

DB_PATH = "product_specs.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor TEXT NOT NULL,
            filename TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_input TEXT NOT NULL,
            response TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

def save_pdf_text_to_db(vendor: str, filename: str, text: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO product_specs (vendor, filename, content) VALUES (?, ?, ?)",
        (vendor, filename, text)
    )
    conn.commit()
    conn.close()

def get_all_product_specs() -> str:
    """合併所有 PDF 文本內容，用於推薦流程 prompt"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT vendor, filename, content FROM product_specs")
    rows = cursor.fetchall()
    conn.close()

    formatted = []
    for vendor, filename, content in rows:
        formatted.append(f"[{vendor}] {filename}\n{content}")
    return "\n\n".join(formatted)

def get_all_product_specs_raw() -> list[tuple[int, str, str, str, None]]:
    """回傳所有資料行 (id, vendor, filename, content, None) → 兼容 UI 展示模組"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, vendor, filename, content FROM product_specs")
    rows = cursor.fetchall()
    conn.close()
    return [(*row, None) for row in rows]  # 加入 None 保持欄位一致

def delete_product_spec_by_id(spec_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM product_specs WHERE id = ?", (spec_id,))
    conn.commit()
    conn.close()

def check_database_status() -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM product_specs")
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def save_query_to_db(user_input: str, response: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO query_history (user_input, response) VALUES (?, ?)", (user_input, response))
    conn.commit()
    conn.close()

def get_all_queries(limit: int = 10) -> list[tuple[str, str]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_input, response FROM query_history ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_pdf_files_with_content() -> list[tuple[int, str, str, str]]:
    """取得所有 PDF 原始資料，用於檢索或分析"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, vendor, filename, content FROM product_specs")
    rows = cursor.fetchall()
    conn.close()
    return rows
