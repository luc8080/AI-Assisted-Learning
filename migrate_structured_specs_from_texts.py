import asyncio
from database import get_all_product_specs_raw, init_db, save_structured_spec_to_db
from spec_classifier import classify_specs_from_text
import sqlite3

DB_PATH = "product_specs.db"

async def migrate_all():
    init_db()
    specs = get_all_product_specs_raw()

    for spec_id, vendor, filename, content, _ in specs:
        print(f"📄 處理檔案：{vendor} - {filename}")
        results = await classify_specs_from_text(content)

        if not results:
            print("⚠️ 沒有擷取到任何規格資料")
            continue

        print(f"➡️ 擷取到 {len(results)} 筆結構化規格（含分類）")
        for item in results:
            save_structured_spec_to_db(item, vendor, filename)

    print("✅ 所有資料已處理完成")

if __name__ == "__main__":
    asyncio.run(migrate_all())
