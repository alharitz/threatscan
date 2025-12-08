import psycopg2
from psycopg2 import sql
import os
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

# The name of the table and column where your CPE strings are stored
CPE_TABLE_NAME = "cpe_entries"
CPE_COLUMN_NAME = "cpe23uri"

CHUNK_SIZE = 100000

# --- 2. CPE PARSING FUNCTION ---

def parse_cpe_2_3(cpe_uri: str) -> dict:
    """
    Parses a CPE 2.3 Formatted String Binding into its components.
    Format: cpe:2.3:<part>:<vendor>:<product>:<version>...
    """
    
    if not cpe_uri.startswith("cpe:2.3:"):
        return {"error": "Invalid CPE 2.3 format"}

    # Split the string by ':'
    parts = cpe_uri.split(':')

    # Basic CPE 2.3 has 12 parts, but we only focus on the first 5 for core data
    if len(parts) < 5:
        return {"error": "CPE string too short"}

    # The components are fixed positions after 'cpe:2.3' (which take up 2 positions)
    # [0] = cpe, [1] = 2.3, [2] = part, [3] = vendor, [4] = product, [5] = version
    
    # We use .replace('_', ' ') to make the product/vendor names more readable
    return {
        "cpe_uri": cpe_uri,
        "part": parts[2],
        "vendor": parts[3].replace('_', ' '),
        "product": parts[4].replace('_', ' '),
        "version": parts[5]
        # U can add the other fields (update, edition, etc.) as needed
    }

# --- 3. DATABASE QUERY & PARSING ---

def stream_and_parse_cpe():
    """
    Connects, uses a server-side cursor to fetch in chunks, and 
    YIELDS parsed data one record at a time.
    """
    conn = None
    total_parsed = 0
    
    try:
        # Establish connection (DB_CONF is assumed to be defined globally)
        conn = psycopg2.connect(**DB_CONF)
        
        # KEY: Create a named cursor for server-side streaming
        with conn.cursor(name="cpe_stream_cursor") as cur:
            # Set the chunk size (CHUNK_SIZE is assumed to be defined globally)
            cur.itersize = CHUNK_SIZE
            
            # Construct a safe SQL query
            query = sql.SQL("SELECT {} FROM {}").format(
                sql.Identifier(CPE_COLUMN_NAME),
                sql.Identifier(CPE_TABLE_NAME)
            )
            
            print(f"Executing query and streaming data in chunks of {CHUNK_SIZE}...")
            cur.execute(query)
            
            # Fetch data in chunks until no more rows are returned
            while True:
                cpe_chunk = cur.fetchmany(cur.itersize)
                
                if not cpe_chunk:
                    break 
                
                # Process the chunk
                for row in cpe_chunk:
                    cpe_string = row[0] 
                    parsed = parse_cpe_2_3(cpe_string) 
                    total_parsed += 1
                    
                    # 💡 FIX: YIELD the result instead of appending to a list
                    yield parsed
        
        print(f"\nFinished streaming. Total records processed: {total_parsed}")
        
    except Exception as e:
        print(f"🚨 An error occurred during processing: {e}")
    finally:
        if conn:
            conn.close()

# --- 4. EXECUTION (Modified for CSV Export) ---
import csv

if __name__ == "__main__":
    
    # 1. Define the output file and fields
    output_filename = "parsed_cpe_data.csv"
    # These fields match the keys returned by parse_cpe_2_3
    fieldnames = ['cpe_uri', 'part', 'vendor', 'product', 'version']
    total_parsed_count = 0

    print("Starting data stream and export to CSV...")
    
    try:
        # 2. Open the CSV file and set up the DictWriter
        with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader() # Write the header row
            
            # 3. Stream data and write it directly to the file
            for record in stream_and_parse_cpe():
                if "error" not in record:
                    writer.writerow(record) # Write the current record to the CSV
                    total_parsed_count += 1
                    
                    # Optional: Print progress every 10,000 records
                    if total_parsed_count % 10000 == 0:
                        print(f"-> Exported {total_parsed_count} records so far...")
                        
    except Exception as e:
        print(f"🚨 Error during export: {e}")
        
    print(f"\n✅ Export complete! Successfully parsed and saved {total_parsed_count} records to {output_filename}")