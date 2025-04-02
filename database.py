import sqlite3

DB_PATH = "product_specs.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # PDF 原始內容表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor TEXT NOT NULL,
            filename TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')

    # 查詢歷史紀錄
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_input TEXT NOT NULL,
            response TEXT NOT NULL
        )
    ''')

    # 結構化產品規格表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS structured_specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_number TEXT NOT NULL,
            vendor TEXT,
            source_filename TEXT,
            impedance REAL,
            test_frequency REAL,
            dcr REAL,
            current REAL,
            temp_min REAL,
            temp_max REAL,
            size TEXT
        )
    ''')

    conn.commit()
    conn.close()

# === PDF 原始內容 ===

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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT vendor, filename, content FROM product_specs")
    rows = cursor.fetchall()
    conn.close()
    return "\n\n".join([f"[{vendor}] {filename}\n{content}" for vendor, filename, content in rows])

def get_all_product_specs_raw() -> list[tuple[int, str, str, str, None]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, vendor, filename, content FROM product_specs")
    rows = cursor.fetchall()
    conn.close()
    return [(*row, None) for row in rows]

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

def get_pdf_files_with_content() -> list[tuple[int, str, str, str]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, vendor, filename, content FROM product_specs")
    rows = cursor.fetchall()
    conn.close()
    return rows

# === 查詢紀錄 ===

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

# === 結構化產品資料 ===

def save_structured_spec_to_db(spec: dict, vendor: str, filename: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO structured_specs (
            part_number, vendor, source_filename,
            impedance, test_frequency, dcr, current,
            temp_min, temp_max, size
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        spec.get("part_number"),
        vendor,
        filename,
        spec.get("impedance"),
        spec.get("test_frequency"),
        spec.get("dcr"),
        spec.get("current"),
        spec.get("temp_min"),
        spec.get("temp_max"),
        spec.get("size")
    ))
    conn.commit()
    conn.close()

def get_all_structured_specs() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM structured_specs")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
