import sqlite3

db_path = "product_specs.db"

def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS product_specs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor TEXT,
        filename TEXT,
        content TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS query_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_input TEXT NOT NULL,
        response TEXT NOT NULL)''')
    conn.commit()
    conn.close()

def save_pdf_text_to_db(vendor, filename, text):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO product_specs (vendor, filename, content) VALUES (?, ?, ?)",
                   (vendor, filename, text))
    conn.commit()
    conn.close()

def get_all_product_specs():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT vendor, filename, content FROM product_specs")
    rows = cursor.fetchall()
    conn.close()
    return "\n".join([f"【{r[0]}】{r[1]}\n{r[2]}" for r in rows])

def get_all_product_specs_raw():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, vendor, filename, content FROM product_specs")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_product_spec_by_id(spec_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM product_specs WHERE id=?", (spec_id,))
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
    cursor.execute("INSERT INTO query_history (user_input, response) VALUES (?, ?)",
                   (user_input, response))
    conn.commit()
    conn.close()

def get_all_queries():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT user_input, response FROM query_history ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows
