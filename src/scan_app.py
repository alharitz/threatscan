import os
from scanner.main_scanner import run_scan_with_progress
from api.main_api import main as process_vulnerabilities
import json

def main():
    print("Starting system scan...")
    try:
        # Run system scan
        scan_results = run_scan_with_progress()
        print("\nScan completed, processing vulnerabilities...")
        
        # Process vulnerabilities
        mitigation_results = process_vulnerabilities(scan_results)
        
        # Save results
        output_dir = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(output_dir, exist_ok=True)
        
        with open(os.path.join(output_dir, "mitigation_report.json"), "w") as f:
            json.dump(mitigation_results, f, indent=2)
            
        print("\nScan and analysis complete!")
        print("Press Enter to exit...")
        input()
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Press Enter to exit...")
        input()

if __name__ == "__main__":
    main()