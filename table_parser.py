# table_parser.py
import pdfplumber

# ✨ 欄位名稱對應表：原始欄位 ➜ 標準欄位
FIELD_MAPPING = {
    "tai-tech part number": "part_number",
    "part number": "part_number",
    "impedance": "impedance",
    "impedance (ω)": "impedance",
    "dc resistance": "dcr",
    "dc resistance (ω)": "dcr",
    "dc resistance (ω) max.": "dcr",
    "rated current": "current",
    "rated current (ma) max.": "current",
    "test frequency": "test_frequency",
    "test frequency (mhz)": "test_frequency",
    "operating temperature": "temp",
    "operating temp. (°c)": "temp"
}

def normalize_headers(headers: list[str]) -> list[str]:
    """根據欄位對應表將原始 header 標準化"""
    normalized = []
    for h in headers:
        if not h:
            normalized.append("")
            continue
        key = h.lower().strip()
        normalized.append(FIELD_MAPPING.get(key, key))  # fallback 保留原欄位
    return normalized

def extract_all_part_rows_from_pdf(pdf) -> list[dict]:
    """
    擷取整份 PDF 中所有產品 row，並將欄位標準化（套用 FIELD_MAPPING）

    Returns:
        list[dict]: 每一筆產品資料
    """
    rows = []
    try:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if not table or len(table) < 2:
                    continue
                raw_headers = table[0]
                headers = normalize_headers(raw_headers)
                for row in table[1:]:
                    if any(row):
                        row_dict = dict(zip(headers, row))
                        rows.append(row_dict)
    except Exception as e:
        print(f"[TableParser] 錯誤：{e}")
    return rows
