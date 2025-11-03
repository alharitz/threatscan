import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_DIR = os.path.join(PROJECT_ROOT, "db")
STORAGE_DIR = os.path.join(PROJECT_ROOT, "storage")

CVE_DATA_DIR = os.path.join(PROJECT_ROOT, "db/data/cve_data")
CPE_DATA_DIR = os.path.join(PROJECT_ROOT, "db/data/cpe_data")

RESULT_STORAGE_DIR = os.path.join(STORAGE_DIR, "results")

LOG_DIR = os.path.join(STORAGE_DIR, "logs")