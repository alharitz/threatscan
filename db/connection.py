# /db/connection.py

from dotenv import load_dotenv
from psycopg2 import pool
import os

load_dotenv()

def get_pool():
    return pool.SimpleConnectionPool(
        1, 5,
        host = os.getenv("PGHOST"),
        port = int(os.getenv("PGPORT", 5432)),
        dbname = os.getenv("PGDATABASE"),
        user = os.getenv("PGUSER"),
        password = os.getenv("PGPASSWORD")
    )