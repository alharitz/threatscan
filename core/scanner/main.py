from utils.logger import setup_logger
from collectors import (
    OSCollector,
    ProgramsCollector,
    PythonCollector,
    JavaScriptCollector,
    PHPCollector,
    PerlCollector,
    RubyCollector,
    RustCollector,
    ProcessCollector,
)
import time

log = setup_logger()
log = log.getChild("scanner")

class Scanner:
    def __init__(self):
        self.complete = 0

        self.system_collectors = {
            "os": OSCollector(),
            "programs": ProgramsCollector(),
            "process": ProcessCollector()
        }

        self.languages_collectors = [
            PythonCollector(),
            JavaScriptCollector(),
            PHPCollector(),
            PerlCollector(),
            RubyCollector(),
            RustCollector()
        ]

        self.counter = self._counter()

    def _counter(self):
        print("⏳ 0%")
        counter = 0
        for _, collector in self.system_collectors.items():
            if collector.detect():
                counter += 1
        
        for collector in self.languages_collectors:
            if collector.detect():
                counter += 1

        return counter

    def progress(self):
        self.complete += 1
        pct = round(self.complete / self.counter * 100)

        print(f"⏳ {pct}%")

    def collect_system(self) -> dict:
        results = {"system": {}}

        for name, collector in self.system_collectors.items():
            detected = collector.detect()

            if detected:
                self.progress()
                try:
                    results["system"][name] = collector.collect()
                except Exception as e:
                    log.error(f"Failed collecting system data for '{name}': {e}", exc_info=True)
                    continue

        return results

    def collect_languages(self) -> dict:
        results = {"languages": []}

        for collector in self.languages_collectors:
            lang = getattr(collector, "language", None)
            try:
                if not collector.detect():
                    continue
                
                self.progress()
                data = collector.collect()

                if isinstance(data, dict) and data:
                    results["languages"].append(data)
                elif isinstance(data, list) and data:
                    results["languages"].extend(data)


            except Exception as e:
                log.error(f"Failed collecting '{lang}': {e}", exc_info=True)
                continue


        return results

    def run(self) -> dict:        
        results = {}

        # merge system results
        system_data = self.collect_system()
        if system_data["system"]:
            results.update(system_data)

        # merge languages results
        language_data = self.collect_languages()
        if language_data["languages"]:
            results.update(language_data)

        return results
