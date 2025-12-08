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
BATCH_SIZE = 1000000

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
    cve_data = item.get("cve", {})    
    cve_id = cve_data.get("id")

    # 1. Get Description
    descriptions = cve_data.get("descriptions", [])
    desc_en = next((d["value"] for d in descriptions if d["lang"] == "en"), None)

    # 2. Get Metrics (Fixed logic)
    metrics = cve_data.get("metrics", {})

    # Handle V3.1 or V3.0
    cvss_v3_metrics = metrics.get("cvssMetricV31") or metrics.get("cvssMetricV30")
    if cvss_v3_metrics:
        # Usually a list, take the first element
        v3_data = cvss_v3_metrics[0].get("cvssData", {})
        cvss_v3_base_score = v3_data.get("baseScore")
        cvss_v3_vector = v3_data.get("vectorString")
        base_severity = v3_data.get("baseSeverity")
    else:
        cvss_v3_base_score = None
        cvss_v3_vector = None
        base_severity = None

    # Handle V2
    cvss_v2_metrics = metrics.get("cvssMetricV2")
    if cvss_v2_metrics:
        v2_data = cvss_v2_metrics[0].get("cvssData", {})
        cvss_v2_base_score = v2_data.get("baseScore")
        cvss_v2_vector = v2_data.get("vectorString")

        if not base_severity:
            base_severity = cvss_v2_metrics[0].get("baseSeverity")
    else:
        cvss_v2_base_score = None
        cvss_v2_vector = None

    return (
        cve_id,
        cve_data.get("sourceIdentifier", "NVD"),
        desc_en.split('.')[0] if desc_en else None, 
        desc_en,
        base_severity,
        cvss_v3_base_score,
        cvss_v3_vector,
        cvss_v2_base_score,
        cvss_v2_vector,
        cve_data.get("published"),
        cve_data.get("lastModified"),
        cve_data.get("vulnStatus"),
        cve_data.get("sourceIdentifier"),
        json.dumps(cve_data.get("weaknesses", [])),
        json.dumps(cve_data.get("remediations", [])), # Note: Remediations often not in standard NVD JSON, but kept if custom
        json.dumps(cve_data.get("references", [])),
        json.dumps(cve_data), # Save the inner cve object as raw data
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
