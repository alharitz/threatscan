import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'sqlite', 'threatscan.sqlite')

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def insert_cpe(cpe_list):

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA synchronous")
        cursor.execute("PRAGMA journal_mode = MEMORY")
        cursor.execute("PRAGMA temp_store = MEMORY")
        cursor.execute("PRAGMA cache_size = 100000")

        cursor.execute("BEGIN TRANSACTION")
        try:
            cursor.executemany('''
                INSERT OR IGNORE INTO cpe (cpe23_name, title, part, vendor, product, version) 
                VALUES (?, ?, ?, ?, ?, ?)
                ''', cpe_list)

            conn.commit()

        except sqlite3.Error as e:
            print(f"❌ Error while inserting CPE into the database ")
        except Exception as e:
            print(e)

# TODO create helper db function as needed 🗒️
