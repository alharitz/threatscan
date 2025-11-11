# main.py

import time
import os
import json
import glob

from utils.logger import setup_logger
from db.connection import init_db_pool, close_db_pool
from core.scanner import Scanner
from core.matcher import Matcher

# 1. Setup logger utama
log = setup_logger()

def run_threatscan():
    """
    Fungsi utama untuk menjalankan seluruh proses scan.
    """
    log.info("==========================================")
    log.info("🚀 ThreatScan Local Vulnerability Scanner")
    log.info("==========================================")
    start_time = time.time()

    try:
        # --- 2. Inisialisasi Database Pool ---
        log.info("Initializing database connection pool...")
        init_db_pool()
        log.info("Database pool initialized.")

        # --- 3. Jalankan Scanner ---
        scanner = Scanner()
        # Ini adalah list JSON panjang berisi SEMUA software
        all_software_list = scanner.run_scan()

        # (Opsional) Simpen hasil mentahnya
        scanner.save_results_to_file(all_software_list, "scan_result_raw.json")

        if not all_software_list:
            log.warning("Scan finished but found no software. Exiting.")
            status = False
            vuln_count = 0
            return

        # --- 4. Jalankan Matcher ---
        log.info(f"Starting vulnerability matching for {len(all_software_list)} items...")
        matcher = Matcher() # Dia otomatis 'minjem' pool yg udah kita buat
        
        # Ini adalah list JSON yg udah di-update dgn key 'vulnerabilities'
        final_report = matcher.find_vulnerabilities(all_software_list)
        vuln_count = sum(1 for item in final_report if item.get("vulnerabilities"))
        status = True

        from utils.paths import RESULT_STORAGE_DIR
        os.makedirs(RESULT_STORAGE_DIR, exist_ok=True)
        existing_reports = glob.glob(os.path.join(RESULT_STORAGE_DIR, "vulnerability_report_*.json"))
        next_id = len(existing_reports) + 1

        log.info("Vulnerability matching complete.")

        # --- 5. Simpen Laporan Final ---
        report_filename = f"vulnerability_report_{next_id}.json"
        report_path = os.path.join(RESULT_STORAGE_DIR, report_filename)
        scanner.save_results_to_file(final_report, report_path)
        log.info("Final vulnerability report saved.")

        # --- 6. Kasih Ringkasan ---
        total_vulnerable_items = sum(1 for item in final_report if item.get("vulnerabilities"))
        log.info("--- 📊 Scan Summary ---")
        log.info(f"   Total items scanned: {len(final_report)}")
        log.info(f"   Items with vulnerabilities: {total_vulnerable_items}")
        log.info("--------------------------")

        # --- 7. Log the scan ---
        scan_log_path = os.path.join(RESULT_STORAGE_DIR, "scan_log.json")
        scan_logs = []

        if os.path.exists(scan_log_path):
            try:
                with open(scan_log_path, "r", encoding="utf-8") as f:
                    scan_logs = json.load(f)
            except json.JSONDecodeError:
                log.warning("scan_log.json corrupted, starting fresh.")
                scan_logs = []

        new_entry = {
            "scan_id": next_id,
            "date_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start_time)),
            "vuln_count": vuln_count,
            "status": status
        }

        scan_logs.insert(0, new_entry)
        with open(scan_log_path, "w", encoding="utf-8") as f:
            json.dump(scan_logs, f, indent=2)

        log.info(f"📝 Logged scan #{next_id} ({vuln_count} vulns)")

    except Exception as e:
        log.error(f"FATAL ERROR during scan: {e}", exc_info=True)
        # ensure failed scans are logged too
        from utils.paths import RESULT_STORAGE_DIR
        os.makedirs(RESULT_STORAGE_DIR, exist_ok=True)
        scan_log_path = os.path.join(RESULT_STORAGE_DIR, "scan_log.json")
        scan_logs = []
        if os.path.exists(scan_log_path):
            try:
                with open(scan_log_path, "r", encoding="utf-8") as f:
                    scan_logs = json.load(f)
            except json.JSONDecodeError:
                scan_logs = []

        new_entry = {
            "scan_id": len(scan_logs) + 1,
            "date_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start_time)),
            "vuln_count": 0,
            "status": False
        }

        scan_logs.insert(0, new_entry)
        with open(scan_log_path, "w", encoding="utf-8") as f:
            json.dump(scan_logs, f, indent=2)

    finally:
        log.info("Closing database pool...")
        close_db_pool()

    end_time = time.time()
    log.info(f"ThreatScan finished. Total time: {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    run_threatscan()