import os
import pytest
import json
from collections import Counter
from collectors import ProgramsCollector
from utils.logger import setup_logger

log = setup_logger()
log = log.getChild("testing")
log = log.getChild("programs_collector")

# DATA EXTRACTOR UNIT TEST
def test_installed_apps():
    collector = ProgramsCollector()

    installed_apps = collector.collect()
    assert isinstance(installed_apps, list)
    assert all(
        isinstance(app, dict)
        and "name" in app
        and "version" in app
        for app in installed_apps
    )

# SAVE DATA EXTRACTOR RESULT
def save_installed_apps():
    collector = ProgramsCollector()
    
    my_data = collector.collect()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "../testing/collector_results/my_installed_apps.json")
    data_path = os.path.normpath(data_path)
    
    try:
        with open(data_path, "w") as f:
            json.dump(my_data, f, indent=4)
        log.info("Installed Apps saved successfully")
    except Exception as e:
        log.error(e)

# COMPARISON BETEWEEN DATA EXTRACTOR AND OSQUERY
def comparing_installed_apps():
    collector = ProgramsCollector()

    my_data = collector.collect()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "../testing/collector_results/osquery_installed_apps.json")
    data_path = os.path.normpath(data_path)

    try:
        with open (data_path) as f:
            osquery_data = json.load(f)
    except FileNotFoundError:
        exit(f"File not found {data_path}")
    except json.JSONDecodeError:
        exit(f"Invalid JSON format {data_path}")
    
    # OSQUERY DATA DEDUPLICATION
    log.info(f"TOTAL_OSQUERY_BEFORE_DEDUP: {len(osquery_data)}")
    osquery_tuples = [tuple(sorted(osquery.items())) for osquery in osquery_data]
    unique_osquery_tuples = list(set(osquery_tuples))
    unique_osquery = [dict(unique_osquery_tuple) for unique_osquery_tuple in unique_osquery_tuples]
    log.info(f"UNIQUE_OSQUERY: {len(unique_osquery)}")

    my_data_tuples = [(app['name'], app['version']) for app in my_data]
    osquery_data_tuples = [(osquery['name'], osquery['version']) for osquery in unique_osquery]

    # COUNTER FOR DUPLICATES DATA OF BOTH DATASET
    count_my_data_tuples = Counter(my_data_tuples)
    count_osquery_data_tuples = Counter(osquery_data_tuples)

    my_data_duplicates = [items for items, count in count_my_data_tuples.items() if count > 1]
    osquery_data_duplicates = [items for items, count in count_osquery_data_tuples.items() if count > 1]
    
    # PERCENTAGE DIFFERENCE IN EACH DATASET
    count_my_data = len(my_data)
    count_osquery_data = len(unique_osquery)
    count_diff = abs(count_my_data - count_osquery_data)
    percentage_difference = count_diff / max(count_my_data, count_osquery_data) * 100

    # SHOWING THE DIFFERENCE IN BOTH DATASET
    my_data_tuples = {(data['name'], data['version']) for data in my_data}
    osquery_data_tuples = {(data['name'], data['version']) for data in osquery_data}

    only_in_my_data = my_data_tuples - osquery_data_tuples
    only_in_osquery_data = osquery_data_tuples - my_data_tuples

    log.info("")
    log.info(f"My Data Extractor Data: {count_my_data}")
    log.info(f"My Data Osquery Data: {count_osquery_data}")
    log.info(f"Count Difference: {count_diff}")
    log.info(f"Difference: {percentage_difference:.2f}%")
    log.info("")
    log.info("Duplicate_my_data:")
    log.info(my_data_duplicates)
    log.info("")
    log.info("Duplicate_osquery_data:")
    log.info(osquery_data_duplicates)
    log.info("")
    log.info("Only in my_data:")
    log.info(only_in_my_data)
    log.info("")
    log.info("Only in osquery_data:")
    log.info(only_in_osquery_data)
    
if __name__ == "__main__":
    comparing_installed_apps()
    save_installed_apps()