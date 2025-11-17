# collectors/languages/javascript_collector.py

from collectors.base_collector import BaseCollector
from utils.logger import setup_logger
from collectors.languages import javascript_parser
from utils.normalize import normalize_name, normalize_version
import shutil
import subprocess
import json

log = setup_logger()
log = log.getChild("collector")
log = log.getChild("Javascript")

class NodeCollector(BaseCollector):
    def detect(self) -> bool:
        return shutil.which("node") is not None
    
    def collect(self) -> list[dict[str, str]]:
        results = [] 

        pm = shutil.which("npm")
        if pm is None:
            return []

        try:
            runtime_version_raw = subprocess.check_output(
                ["node", "--version"],
                text=True,
                stderr=subprocess.STDOUT
            ).strip()
            runtime_version = runtime_version_raw.lstrip("v")
            runtime_name = "Node.js"

            results.append({
                "name": runtime_name,
                "version": runtime_version,
                "normalized_name": normalize_name(runtime_name),
                "normalized_version": normalize_version(runtime_version),
                "type": "language_runtime"
            })

            output = subprocess.check_output(
                [pm, "ls", "-g", "--json", "--depth=0"],
                text=True,
                stderr=subprocess.STDOUT
            ).strip()

            json_output = json.loads(output)
            packages = javascript_parser.nodeParser(json_output.get("dependencies", {}), log)

            for pkg in packages:
                if not pkg.get("name") or not pkg.get("version"):
                    continue
                pkg['normalized_name'] = normalize_name(pkg['name'])
                pkg['normalized_version'] = normalize_version(pkg['version'])
                pkg['type'] = 'js_package'
                pkg['parent_language_version'] = runtime_version
                results.append(pkg)
            
            return results

        except Exception as e:
            log.error(f"Failed collecting Javascript (Node) Packages: {e}", exc_info=True)
            return []

class BunCollector(BaseCollector):
    def detect(self) -> bool:
        return shutil.which("bun") is not None

    def collect(self) -> list[dict[str, str]]:
        results = []

        try:
            runtime_version = subprocess.check_output(
                ["bun", "--version"],
                text=True,
                stderr=subprocess.STDOUT
            ).strip()
            runtime_name = "Bun"

            results.append({
                "name": runtime_name,
                "version": runtime_version,
                "normalized_name": normalize_name(runtime_name),
                "normalized_version": normalize_version(runtime_version),
                "type": "language_runtime"
            })

            process = subprocess.run(
                ["bun", "pm", "ls", "--global", "--all"],
                text=True,
                capture_output=True
            )

            if process.returncode != 0:
                log.error(f"Failed collecting Javascript (Bun) Packages: {process.stderr or process.stdout}")
                return results

            output = (process.stdout or "").strip()
            packages = javascript_parser.bunParser(output, log)

            for pkg in packages:
                if not pkg.get("name") or not pkg.get("version"):
                    continue
                pkg['normalized_name'] = normalize_name(pkg['name'])
                pkg['normalized_version'] = normalize_version(pkg['version'])
                pkg['type'] = 'js_package'
                pkg['parent_language_version'] = runtime_version
                results.append(pkg)
            
            return results
            
        except Exception as e:
            log.error(f"Failed collecting Javascript (Bun) Packages: {e}", exc_info=True)
            return []

class JavaScriptCollector(BaseCollector):
    def __init__(self):
        self.subCollectors = [BunCollector(), NodeCollector()]

    def detect(self) -> bool:
        return any(subCollector.detect() for subCollector in self.subCollectors)
    
    def collect(self) -> list[dict]:
        results = []

        for subCollector in self.subCollectors:
            results.extend(subCollector.safe_collect())

        return results