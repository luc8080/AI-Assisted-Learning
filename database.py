# === 檔案路徑：database.py
# === 功能說明：
# 管理 SQLite 資料庫，包含 PDF 原文儲存、產品規格結構化資料、查詢紀錄等。
# 支援自動初始化、欄位補全與結構一致性處理。
# === 最後更新：2025-04-13

import sqlite3

DB_PATH = "product_specs.db"

# === 資料表初始化 ===
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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS structured_specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_number TEXT,
            impedance REAL,
            dcr REAL,
            current REAL,
            test_frequency REAL,
            temp_min REAL,
            temp_max REAL,
            size TEXT,
            vendor TEXT,
            category TEXT,
            application TEXT,
            source_filename TEXT,
            material TEXT,
            packaging TEXT,
            tolerance TEXT,
            rated_voltage REAL,
            inductance REAL
        )
    ''')

    conn.commit()
    conn.close()

# === 原始 PDF 文本儲存 ===
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

# === 查詢紀錄管理 ===
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

# === 結構化產品資料儲存與查詢 ===
def save_structured_spec_to_db(spec: dict, vendor: str, source_filename: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 補齊欄位預設值
    defaults = {
        "impedance": None,
        "dcr": None,
        "current": None,
        "test_frequency": None,
        "temp_min": -40,
        "temp_max": 125,
        "category": "Ferrite Bead",
        "application": None,
        "material": None,
        "packaging": None,
        "tolerance": None,
        "rated_voltage": None,
        "inductance": None
    }
    for key, default in defaults.items():
        spec.setdefault(key, default)

    cursor.execute('''
        INSERT INTO structured_specs (
            part_number, impedance, dcr, current, test_frequency,
            temp_min, temp_max, size, vendor, category,
            application, source_filename, material, packaging,
            tolerance, rated_voltage, inductance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        spec.get("part_number"),
        spec.get("impedance"),
        spec.get("dcr"),
        spec.get("current"),
        spec.get("test_frequency"),
        spec.get("temp_min"),
        spec.get("temp_max"),
        spec.get("size"),
        vendor,
        spec.get("category"),
        spec.get("application"),
        source_filename,
        spec.get("material"),
        spec.get("packaging"),
        spec.get("tolerance"),
        spec.get("rated_voltage"),
        spec.get("inductance")
    ))

    conn.commit()
    conn.close()

def get_all_structured_specs() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM structured_specs")
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    conn.close()
    return [dict(zip(columns, row)) for row in rows]

def delete_structured_spec_by_id(spec_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM structured_specs WHERE id = ?", (spec_id,))
    conn.commit()
    conn.close()
