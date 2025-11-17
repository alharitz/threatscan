# /db/init_db.py

import os
from dotenv import load_dotenv
from psycopg2 import connect

load_dotenv()

# Database Config
DB_CONF = dict(
    dbname=os.getenv("PGDATABASE"),
    user=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD", "postgres"),
    host=os.getenv("PGHOST", "localhost"),
    port=int(os.getenv("PGPORT", 5432)),
)

def init_cpe_table():
    """Create the CPE table if it doesn't exist."""
    schema = """
    CREATE TABLE IF NOT EXISTS cpe_entries (
        id SERIAL PRIMARY KEY,
        cpe23uri TEXT UNIQUE,
        part TEXT,
        vendor TEXT,
        product TEXT,
        version TEXT,
        update TEXT,
        edition TEXT,
        language TEXT,
        sw_edition TEXT,
        target_sw TEXT,
        target_hw TEXT,
        other TEXT,
        deprecated BOOLEAN DEFAULT FALSE,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_cpe_vendor_product_version ON cpe_entries (vendor, product, version);",
        "CREATE INDEX IF NOT EXISTS idx_cpe_product_trgm ON cpe_entries USING gin (product gin_trgm_ops);"
    ]

    conn = connect(**DB_CONF)
    cur = conn.cursor()

    try:
        cur.execute(schema)
        for idx in indexes:
            cur.execute(idx)
        conn.commit()
        print("✅ Success: cpe_entries table initialized successfully.")
    except Exception as e:
        conn.rollback()
        print("❌ Error initializing cpe_entries:", e)
    finally:
        cur.close()
        conn.close()