# migrate_structured_specs_from_texts.py
import asyncio
from database import get_all_product_specs_raw, init_db
from batch_spec_extractor import extract_multiple_specs_from_text
import sqlite3

DB_PATH = "product_specs.db"

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

async def migrate_all():
    init_db()
    specs = get_all_product_specs_raw()

    for spec_id, vendor, filename, content, _ in specs:
        print(f"📄 處理檔案：{vendor} - {filename}")
        results = await extract_multiple_specs_from_text(content)

        print(f"➡️ 擷取到 {len(results)} 筆結構化規格")
        for item in results:
            save_structured_spec_to_db(item, vendor, filename)

    print("✅ 所有資料已處理完成")

if __name__ == "__main__":
    asyncio.run(migrate_all())
