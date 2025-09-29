from collectors.module.base_collector import BaseCollector
from utils.logger import setup_logger
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
            runtime_version = subprocess.check_output(
                ["node", "--version"],
                text=True,
                stderr=subprocess.STDOUT
            ).strip()

            output = subprocess.check_output(
                    [pm, "ls", "-g", "--json", "--depth=0"],
                    text=True,
                    stderr=subprocess.STDOUT
                ).strip()

            json_output = json.loads(output)
            packages = json_output.get("dependencies", {})

            parsed_packages = []
            for pkg_name, pkg_info in packages.items():
                name = pkg_name.lstrip("@").strip()
                version = (pkg_info.get("version") or "").strip() if isinstance(pkg_info, dict) else ""

                parsed_packages.append({
                    "name": name,
                    "version": version
                })

            results.append({
                "runtime": "nodejs",
                "runtime_version": runtime_version.lstrip("v"),
                "packages": parsed_packages
            })

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

            proc = subprocess.run(
                    ["bun", "pm", "ls", "--global", "--all"],
                    text=True,
                    capture_output=True
                )

            outputs = (proc.stdout or proc.stderr or "").strip()
            if proc.returncode != 0:
                log.error(f"Failed collecting Javascript (Bun) Packages: {proc.returncode}", exc_info=True)

            lines = outputs.splitlines()
            packages_location = lines[0].strip()

            packages = []
            for line in lines[1:]:
                _, clean_line = line.split(" ", 1)

                name, version = clean_line.split("@", 1)
                packages.append({
                    "name": name,
                    "version": version
                })
                

            results.append({
                "runtime": "bun",
                "runtime_version": runtime_version,
                "packages": packages
            })
        
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
        runtimes = []

        for subCollector in self.subCollectors:
            if subCollector.detect():
                runtimes.extend(subCollector.collect())

        results.append({
            "language": "javascript",
            "runtimes": runtimes
        })

        return results