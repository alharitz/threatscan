# main.py

import time
import os
import json
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
        # Panggil ini SEKALI AJA di awal
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
            return

        # --- 4. Jalankan Matcher ---
        log.info(f"Starting vulnerability matching for {len(all_software_list)} items...")
        matcher = Matcher() # Dia otomatis 'minjem' pool yg udah kita buat
        
        # Ini adalah list JSON yg udah di-update dgn key 'vulnerabilities'
        final_report = matcher.find_vulnerabilities(all_software_list)
        log.info("Vulnerability matching complete.")

        # --- 5. Simpen Laporan Final ---
        scanner.save_results_to_file(final_report, "vulnerability_report.json")
        log.info("Final vulnerability report saved.")

        # --- 6. Kasih Ringkasan ---
        total_vulnerable_items = sum(1 for item in final_report if item.get("vulnerabilities"))
        log.info("--- 📊 Scan Summary ---")
        log.info(f"   Total items scanned: {len(final_report)}")
        log.info(f"   Items with vulnerabilities: {total_vulnerable_items}")
        log.info("--------------------------")

        # --- 7. Log the scan ---
        log.info("Logging scan result...")
        from utils.paths import RESULT_STORAGE_DIR
        scan_log_path = os.path.join(RESULT_STORAGE_DIR, 'scan_log.json')
        
        # Create the directory if it doesn't exist
        os.makedirs(RESULT_STORAGE_DIR, exist_ok=True)

        scan_logs = []
        if os.path.exists(scan_log_path):
            with open(scan_log_path, 'r', encoding='utf-8') as f:
                try:
                    scan_logs = json.load(f)
                except json.JSONDecodeError:
                    log.warning("scan_log.json is corrupted. Starting with an empty log.")
                    scan_logs = []
        
        scan_id = f"#{len(scan_logs):04d}"
        
        new_log_entry = {
            "scan_id": scan_id,
            "date_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time)),
            "vulnerabilities_found": total_vulnerable_items,
            "status": "Completed",
            "report_url": "/result"
        }
        
        scan_logs.insert(0, new_log_entry)
        
        with open(scan_log_path, 'w', encoding='utf-8') as f:
            json.dump(scan_logs, f, indent=4)
            
        log.info(f"Scan result logged to {scan_log_path}")

    except Exception as e:
        log.error(f"FATAL ERROR during scan: {e}", exc_info=True)
    
    finally:
        log.info("Closing database connection pool...")
        close_db_pool()

    end_time = time.time()
    log.info(f"ThreatScan finished. Total time: {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    run_threatscan()