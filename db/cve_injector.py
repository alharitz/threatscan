# /db/cve_injector.py

import os
import json
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_batch
from glob import glob

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
FOLDER = "./data/cve_data"
GLOB_PATTERN = "nvdcve-2.0-*.json"
BATCH_SIZE = 500000

# Query
INSERT_SQL = """
    INSERT INTO cve_entries (
        cve_id, source, summary, details,
        base_severity,
        cvss_v3_base_score, cvss_v3_vector,
        cvss_v2_base_score, cvss_v2_vector,
        published_at, modified_at,
        vuln_status, source_identifier,
        weaknesses, remediations,
        references_data, raw_data
    ) VALUES (
        %s, %s, %s, %s,
        %s, %s, %s,
        %s, %s,
        %s, %s,
        %s, %s,
        %s, %s,
        %s, %s
    )
    ON CONFLICT (cve_id) DO UPDATE SET
        summary = EXCLUDED.summary,
        details = EXCLUDED.details,
        base_severity = EXCLUDED.base_severity,
        cvss_v3_base_score = EXCLUDED.cvss_v3_base_score,
        cvss_v3_vector = EXCLUDED.cvss_v3_vector,
        cvss_v2_base_score = EXCLUDED.cvss_v2_base_score,
        cvss_v2_vector = EXCLUDED.cvss_v2_vector,
        published_at = EXCLUDED.published_at,
        modified_at = EXCLUDED.modified_at,
        vuln_status = EXCLUDED.vuln_status,
        source_identifier = EXCLUDED.source_identifier,
        weaknesses = EXCLUDED.weaknesses,
        remediations = EXCLUDED.remediations,
        references_data = EXCLUDED.references_data,
        raw_data = EXCLUDED.raw_data,
        updated_at = now();
"""

def row_from_cve(item):
    cve_id = item["cve"]["id"]
    descriptions = item["cve"].get("descriptions", [])
    desc_en = next((d["value"] for d in descriptions if d["lang"] == "en"), None)

    metrics = item.get("metrics", {})
    cvss_v3 = (metrics.get("cvssMetricV31") or [{}])[0].get("cvssData", {})
    cvss_v2 = (metrics.get("cvssMetricV2") or [{}])[0].get("cvssData", {})

    return (
        cve_id,
        item.get("cve", {}).get("sourceIdentifier", "NVD"),
        desc_en.split('.')[0] if desc_en else None,        # summary
        desc_en,
        cvss_v3.get("baseSeverity"),
        cvss_v3.get("baseScore"),
        cvss_v3.get("vectorString"),
        cvss_v2.get("baseScore"),
        cvss_v2.get("vectorString"),
        item.get("published"),
        item.get("lastModified"),
        item.get("vulnStatus"),
        item.get("cve", {}).get("sourceIdentifier"),
        json.dumps(item.get("weaknesses", [])),
        json.dumps(item.get("remediations", [])),
        json.dumps(item.get("references", [])),
        json.dumps(item),
    )

def process_file(cur, filepath):
    inserted = 0
    rows = []

    print(f"📄 Reading {os.path.basename(filepath)} ...")
    with open(filepath, "rt", encoding="utf-8") as f:
        data = json.load(f)
        for item in data.get("vulnerabilities", []):
            rows.append(row_from_cve(item))
            if len(rows) >= BATCH_SIZE:
                execute_batch(cur, INSERT_SQL, rows, page_size=200)
                inserted += len(rows)
                print(f"  -> {inserted} rows inserted...")
                rows = []

    if rows:
        execute_batch(cur, INSERT_SQL, rows, page_size=200)
        inserted += len(rows)

    return inserted

def inject_cve_data(folder: str = FOLDER):
    files = sorted(glob(os.path.join(folder, GLOB_PATTERN)))
    if not files:
        print(f"⚠️  No CVE files found in: {folder}")
        return

    conn = psycopg2.connect(**DB_CONF)
    cur = conn.cursor()
    total = 0

    try:
        for fp in files:
            print(f"📦 Processing {os.path.basename(fp)}")
            count = process_file(cur, fp)
            conn.commit()
            total += count
            print(f"✅ Done {os.path.basename(fp)} ({count} inserted, total {total})")
    except Exception as e:
        conn.rollback()
        print("❌ Error:", e)
    finally:
        cur.close()
        conn.close()

    print(f"\n🎯 CVE ingest finished. Total inserted: {total}")

if __name__ == "__main__":
    inject_cve_data()
