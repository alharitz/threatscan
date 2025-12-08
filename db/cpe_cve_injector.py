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
    
    # 🔍 Verification Counters
    count_exact = 0
    count_ranges = 0

    vulns = data.get("vulnerabilities", [])
    for v in vulns:
        cve_object = v.get("cve", {})
        if not cve_object: continue 

        cve_id = cve_object.get("id")
        if not cve_id: continue

        configs = cve_object.get("configurations", [])

        for config in configs: 
            for node in config.get("nodes", []):
                # NOTE: Sometimes NVD puts cpeMatch inside 'children' for complex logic
                # But for standard scanning, checking top-level cpeMatch is usually enough.
                for m in node.get("cpeMatch", []):
                    
                    cpe_uri = m.get("criteria") 
                    if not cpe_uri: continue 

                    v_start_inc = m.get("versionStartIncluding")
                    v_start_exc = m.get("versionStartExcluding")
                    v_end_inc = m.get("versionEndIncluding")
                    v_end_exc = m.get("versionEndExcluding")

                    # 🔍 Check if we found a range
                    if any([v_start_inc, v_start_exc, v_end_inc, v_end_exc]):
                        count_ranges += 1
                    else:
                        count_exact += 1

                    rows.append((
                        cve_id,
                        cpe_uri,
                        v_start_inc,
                        v_start_exc,
                        v_end_inc,
                        v_end_exc,
                        m.get("vulnerable", True),
                        json.dumps(m)
                    ))
                    
                    if len(rows) >= BATCH_SIZE:
                        execute_batch(cur, INSERT_SQL, rows, page_size=BATCH_SIZE)
                        inserted += len(rows)
                        print(f"   -> inserted {inserted}...")
                        rows = []

    if rows:
        execute_batch(cur, INSERT_SQL, rows, page_size=BATCH_SIZE)
        inserted += len(rows)

    # 📊 Print the stats for this file
    print(f"   📊 Stats for {os.path.basename(filepath)}: Ranges Found: {count_ranges} | Exact Matches: {count_exact}")
    
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