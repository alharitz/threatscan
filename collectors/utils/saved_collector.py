from core.scanner.main import Scanner
from utils.logger import setup_logger
import os
import json

log = setup_logger()
log = log.getChild("testing")

def save_all(results):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "../../storage/raw/all_collector.json")
    data_path = os.path.normpath(data_path) 

    try:
        with open(data_path, "w") as f:
            json.dump(results, f, indent=4)
            log.info("All collector_results successfully saved")
    except Exception as e:
        log.error(e)