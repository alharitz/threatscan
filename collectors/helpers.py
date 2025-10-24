from utils.paths import RAW_STORAGE_DIR
from utils.logger import setup_logger
import os
import json

log = setup_logger()
log = log.getChild("testing")

def save_all(results):
    data_path = os.path.join(RAW_STORAGE_DIR, "all_collector.json")

    try:
        os.makedirs(RAW_STORAGE_DIR, exist_ok=True)

        with open(data_path, "w") as f:
            json.dump(results, f, indent=4)
            log.info(f"All collector results successfully saved to {data_path}")
    except Exception as e:
        log.error(e)