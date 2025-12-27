import psycopg2
from db.connection import get_db_connection

def test_connection():
    print("⚡ Connecting to DB...")
    conn = get_db_connection().getconn()
    
    try:
        with conn.cursor() as cur:
            # 1. Check Row Count
            cur.execute("SELECT count(*) FROM cpe_entries;")
            count = cur.fetchone()[0]
            print(f"📊 Total Rows in 'cpe_entries': {count}")
            
            if count == 0:
                print("❌ ERROR: Your database is empty! Run your NVD importer.")
                return

            # 2. Check a Search Term that SHOULD work
            search_term = "python"
            print(f"\n🔍 Testing Search for '{search_term}'...")
            
            # Force low threshold
            cur.execute("SET pg_trgm.similarity_threshold = 0.05;")
            
            # Run the EXACT query used in Matcher
            query = """
                SELECT product, similarity(product, %s) as score 
                FROM cpe_entries 
                WHERE product %% %s  -- <--- DOUBLE PERCENT HERE
                ORDER BY score DESC 
                LIMIT 5
            """
            cur.execute(query, (search_term, search_term))
            results = cur.fetchall()
            
            if not results:
                print("❌ Search FAILED (0 matches).")
                print("   Hypothesis: Trigram index might be broken.")
                
                # Fallback test: ILIKE
                print("   👉 Trying fallback 'ILIKE' search...")
                cur.execute("SELECT product FROM cpe_entries WHERE product ILIKE %s LIMIT 3", (f"%{search_term}%",))
                print(f"   👉 ILIKE Results: {cur.fetchall()}")
            else:
                print(f"✅ Search SUCCESS! Found: {results}")

    except Exception as e:
        print(f"💥 CRASH: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_connection()