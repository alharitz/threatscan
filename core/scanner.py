# core/scanner.py

from utils.logger import setup_logger
from utils.paths import RAW_STORAGE_DIR
import json
import os

# System collectors
from collectors.system.os_collector import OSCollector
from collectors.system.programs_collector import ProgramsCollector
from collectors.system.processes_collector import ProcessCollector 

# Language collectors
from collectors.languages.python_collector import PythonCollector
from collectors.languages.javascript_collector import JavaScriptCollector
from collectors.languages.php_collector import PHPCollector
from collectors.languages.ruby_collector import RubyCollector
from collectors.languages.perl_collector import PerlCollector
from collectors.languages.rust_collector import RustCollector

log = setup_logger()
log = log.getChild("scanner")

class Scanner:
    def __init__(self):
        """
        Daftarin semua collector yang mau kita pake.
        """
        self.collectors = [
            OSCollector(),
            ProgramsCollector(),
            ProcessCollector(),
            PythonCollector(),
            JavaScriptCollector(),
            PHPCollector(),
            RubyCollector(),
            PerlCollector(),
            RustCollector(),
        ]
        log.info(f"Scanner initialized with {len(self.collectors)} collectors.")

    def run_scan(self) -> list[dict]:
        """
        Menjalankan semua collector dan menggabungkan hasilnya.
        """
        log.info("🚀 Starting full system scan...")
        all_software_results = []

        for collector in self.collectors:
            collector_name = collector.__class__.__name__
            
            log.info(f"🔍 Running collector: {collector_name}...")

            try:
                results = collector.safe_collect()
                if results:
                    log.info(f"✅ Finished {collector_name}. Found {len(results)} items.")
                    all_software_results.extend(results)
                else:
                    log.info(f"⚪ Finished {collector_name}. No items found.")
            
            except Exception as e:
                log.error(f"❌ CRITICAL ERROR in {collector_name}: {e}", exc_info=True)

        log.info(f"🎉 Full scan finished. Total items found: {len(all_software_results)}")
        return all_software_results

    def save_results_to_file(self, results: list[dict], filename: str = "scan_result.json"):
        """
        Menyimpan hasil scan final ke file JSON.
        """
        if not results:
            log.warning("Scan result is empty, skipping save.")
            return

        save_path = os.path.join(RAW_STORAGE_DIR, filename)
        
        try:
            os.makedirs(RAW_STORAGE_DIR, exist_ok=True)
            
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=4)
            
            log.info(f"💾 Scan results successfully saved to: {save_path}")
        
        except Exception as e:
            log.error(f"Failed to save scan results: {e}", exc_info=True)