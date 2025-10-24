# db/connection.py

from dotenv import load_dotenv
from psycopg2 import pool
import os
import sys
from utils.logger import setup_logger 

load_dotenv()
log = setup_logger().getChild("db")

_db_pool = None

def init_db_pool():
    """
    Create pool ONCE
    Call from main.py when app starts running.
    """
    global _db_pool

    if _db_pool:
        log.warning("Database pool already initialized.")
        return

    try:
        _db_pool = pool.SimpleConnectionPool(
            1, 5, 
            host = os.getenv("PGHOST"),
            port = int(os.getenv("PGPORT", 5432)),
            dbname = os.getenv("PGDATABASE"),
            user = os.getenv("PGUSER"),
            password = os.getenv("PGPASSWORD")
        )
        log.info("Database connection pool initialized (Min: 1, Max: 5).")
        
    except Exception as e:
        log.fatal(f"Failed to initialize database pool: {e}", exc_info=True)
        sys.exit(1)

def get_db_connection():
    global _db_pool

    if _db_pool is None:
        log.info("Pool not initialized (called directly?). Initializing now...")
        init_db_pool()

    return _db_pool 

def close_db_pool():
    global _db_pool
    if _db_pool:
        _db_pool.closeall()
        _db_pool = None
        log.info("Database connection pool closed.")