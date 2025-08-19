from scanner.data_extractor import run_scan, total_data
import time
import threading
import os
import json

def run_scan_with_progress():
    try:
        # Start the scan
        scan_thread = threading.Thread(target=run_scan)
        scan_thread.start()

        # Monitor progress while scan is running
        start_time = time.time()
        while scan_thread.is_alive():
            progress = (total_data["completed"] / total_data["total"]) * 100 if total_data["total"] > 0 else 0
            print(f"Scan progress: {progress:.1f}%")
            time.sleep(0.5)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Scan time: {elapsed_time:.4f} seconds")
        
        # Wait for scan to complete
        scan_thread.join()

        # Get the results (already parsed in data_extractor.py)
        results = total_data["data"]

        if not results:
            raise Exception("No data collected during scan")
        return results
    
    except Exception as e:
        print(f"Error in scan process: {str(e)}")
        return {"error": str(e)}

def main():
    return run_scan_with_progress()
