import sqlite3
from db import db

def init_cpe_table():
    print("Initialize DB...")

    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS cpe(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cpe23_name TEXT NOT NULL UNIQUE,
                    title TEXT,
                    part TXT,
                    vendor TEXT,
                    product TEXT,
                    version TEXT
                )
            '''
            )

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_part ON cpe (part)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_vendor ON cpe (vendor)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_product ON cpe (product)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_version ON cpe (version)')

            conn.commit()
            print("✅ DB initialized successfully")
    except sqlite3.Error:
        print(f"❌ Error while initializing the database")
