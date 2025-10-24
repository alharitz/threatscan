# /db/cpe_cve_injector.py

from glob import glob
import json
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_batch

load_dotenv()

# Database config
DB_CONF = dict(
    dbname=os.getenv("PGDATABASE"),
    user=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD"),
    host=os.getenv("PGHOST", "localhost"),
    port=int(os.getenv("PGPORT", 5432)),
)

# Load file
FOLDER = "./data/cve_data"
GLOB_PATTERN = "nvdcve-2.0-*.json"
BATCH_SIZE = 500000

# Query 
INSERT_SQL = """
    INSERT INTO cve_cpe_entries (
        cve_id, cpe_uri,
        version_start_including, version_start_excluding,
        version_end_including, version_end_excluding,
        vulnerable, match_criteria
    ) VALUES (
        %s, %s,
        %s, %s,
        %s, %s,
        %s, %s
    ) 
    ON CONFLICT (
        cve_id, 
        cpe_uri,
        COALESCE(version_start_including, ''),
        COALESCE(version_start_excluding, ''),
        COALESCE(version_end_including, ''),
        COALESCE(version_end_excluding, '')
    )
    DO NOTHING;
"""

def process_file(cur, filepath):
    """Parse 1 CVE file and extract CVE↔CPE mapping"""

    with open(filepath, "rt", encoding="utf-8") as f:
        data = json.load(f)

    inserted = 0
    rows = []

    vulns = data.get("vulnerabilities", [])
    for v in vulns:
        cve_object = v.get("cve", {})
        if not cve_object:
            continue # Skip kalau data aneh

        cve_id = cve_object.get("id")
        if not cve_id:
            continue

        configs = cve_object.get("configurations", [])

        for config in configs: 
            for node in config.get("nodes", []):
                for m in node.get("cpeMatch", []):
                    
                    # 'criteria' adalah key buat CPE URI di feed ini
                    cpe_uri = m.get("criteria") 
                    if not cpe_uri:
                        continue # Skip kalau gaada CPE URI

                    rows.append((
                        cve_id,
                        cpe_uri, # <-- Pakai variabel yg udah dicek
                        m.get("versionStartIncluding"),
                        m.get("versionStartExcluding"),
                        m.get("versionEndIncluding"),
                        m.get("versionEndExcluding"),
                        m.get("vulnerable", True),
                        json.dumps(m)
                    ))
                    
                    # Logika batch-ing, udah bener!
                    if len(rows) >= BATCH_SIZE:
                        execute_batch(cur, INSERT_SQL, rows, page_size=BATCH_SIZE)
                        inserted += len(rows)
                        print(f"   -> inserted {inserted} so far from {os.path.basename(filepath)}")
                        rows = []

    # Masukin sisa data yg belum ke-batch
    if rows:
        execute_batch(cur, INSERT_SQL, rows, page_size=BATCH_SIZE)
        inserted += len(rows)

    return inserted

def inject_cpe_cve_data(folder: str = FOLDER):
    """Process all match chunk files and inject them into PostgreSQL."""

    search_path = os.path.join(folder, GLOB_PATTERN)
    files = sorted(glob(search_path))

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

    print(f"\n🎯 Match ingest finished. Total inserted: {total}")

if __name__ == "__main__":
    inject_cpe_cve_data()