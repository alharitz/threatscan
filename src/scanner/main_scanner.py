from scanner.data_extractor import run_scan, total_data
import api.main_api as main_api
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
        while scan_thread.is_alive():
            progress = (total_data["completed"] / total_data["total"]) * 100 if total_data["total"] > 0 else 0
            print(f"Scan progress: {progress:.1f}%")
            time.sleep(0.5)

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

# def main():
#     results = run_scan_with_progress()

if __name__ == "__main__":
    print("Starting system scan...")
    
    try:
        # Run the scan with progress monitoring
        results = run_scan_with_progress()
        
        # report = main_api.main(results)

        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Save both raw and parsed results
        parsed_output_file = os.path.join(output_dir, "parsed_scan_results.json")
            
        # Save parsed results
        with open(parsed_output_file, "w") as f:
            json.dump(results, f, indent=4)
            
        print(f"\nScan complete!")
        print(f"Parsed results saved to: {parsed_output_file}")
        
    except Exception as e:
        print(f"Error during scan: {str(e)}")