from collectors import ProcessCollector
from utils.logger import setup_logger
import os
import json

log = setup_logger()
log = log.getChild("testing")
log = log.getChild("process_collector")

def test_process_collector():
    collector = ProcessCollector()
    results = collector.collect()
    
    log.info(f"Process Detection: {collector.detect()}")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "../storage/testing/collector_results/process_info.json")
    data_path = os.path.normpath(data_path) 

    try:
        with open(data_path, "w") as f:
            json.dump(results, f, indent=4)
            log.info("Successfully saved process list")
    except Exception as e:
        log.error(e)


if __name__ == "__main__":
    test_process_collector()
