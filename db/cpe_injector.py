# /db/cpe_injector.py

import os
import json
import psycopg2
from psycopg2.extras import execute_batch
from glob import glob
from dotenv import load_dotenv

load_dotenv()

# Database config
DB_CONF = dict(
    dbname=os.getenv("PGDATABASE"),
    user=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD"),
    host=os.getenv("PGHOST", "localhost"),
    port=int(os.getenv("PGPORT", 5432)),
)

# Load data
FOLDER = "./data/cpe_data"
GLOB_PATTERN = "nvdcpe-2.0-chunk-*.json"
BATCH_SIZE = 10000

# Query
INSERT_SQL = """
    INSERT INTO cpe_entries (
        cpe23uri, part, vendor, product, version, update, edition, language,
        sw_edition, target_sw, target_hw, other, deprecated, title
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT (cpe23uri) DO NOTHING;
"""

def row_from_product(prod):
    """Extract a single CPE row tuple from a product JSON node."""
    cpe = prod.get("cpe", {}) or {}
    cpe23uri = cpe.get("cpeName")

    title = None
    titles = cpe.get("titles") or []
    if titles:
        first = titles[0]
        if isinstance(first, dict):
            title = first.get("title")

    deprecated = cpe.get("deprecated", False)
    parts = cpe23uri.split(":") if cpe23uri else []

    return (
        cpe23uri,
        parts[2] if len(parts) > 2 else None,
        parts[3] if len(parts) > 3 else None,
        parts[4] if len(parts) > 4 else None,
        parts[5] if len(parts) > 5 else None,
        parts[6] if len(parts) > 6 else None,
        parts[7] if len(parts) > 7 else None,
        parts[8] if len(parts) > 8 else None,
        parts[9] if len(parts) > 9 else None,
        parts[10] if len(parts) > 10 else None,
        parts[11] if len(parts) > 11 else None,
        parts[12] if len(parts) > 12 else None,
        deprecated,
        title,
    )


def process_file(cur, filepath):
    """Insert all CPE rows from one chunk file."""
    inserted = 0
    rows = []

    with open(filepath, "rt", encoding="utf-8") as f:
        obj = json.load(f)
        products = obj.get("products", []) or []

        for p in products:
            rows.append(row_from_product(p))
            if len(rows) >= BATCH_SIZE:
                execute_batch(cur, INSERT_SQL, rows, page_size=500)
                inserted += len(rows)
                print(f"  -> {inserted} rows inserted from {os.path.basename(filepath)}")
                rows = []

    if rows:
        execute_batch(cur, INSERT_SQL, rows, page_size=500)
        inserted += len(rows)

    return inserted


def inject_cpe_chunks(folder: str = FOLDER):
    """Process all chunk files and inject them into PostgreSQL."""
    files = sorted(glob(os.path.join(folder, GLOB_PATTERN)))
    if not files:
        print(f"⚠️  No chunk files found in: {folder}")
        return

    conn = psycopg2.connect(**DB_CONF)
    cur = conn.cursor()
    total = 0

    try:
        for fp in files:
            print(f"📦 Processing {os.path.basename(fp)} ...")
            count = process_file(cur, fp)
            conn.commit()
            total += count
            print(f"✅ Finished {os.path.basename(fp)} ({count} inserted, total {total})")
    except Exception as e:
        conn.rollback()
        print("❌ Error:", e)
    finally:
        cur.close()
        conn.close()

    print(f"\n🎯 Done. Total inserted: {total}")


# Allow Direct Run
if __name__ == "__main__":
    inject_cpe_chunks()