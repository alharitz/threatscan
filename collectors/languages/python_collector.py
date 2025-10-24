# collectors/languages/python_collector.py

from collectors.base_collector import BaseCollector
from utils.logger import setup_logger
from collectors.languages import python_parser
import subprocess
import shutil
from utils.normalize import normalize_name, normalize_version

log = setup_logger()
log = log.getChild("collector")
log = log.getChild("python")

class PythonCollector(BaseCollector):
    def __init__(self):
        self.interpreters = self._find_my_pythons()

    def _find_my_pythons(self):
        candidates = ["python", "python2", "python3"]
        found = []

        for candidate in candidates:
            path = shutil.which(candidate)
            if path and path not in found and "WindowsApps" not in path.lower():
                found.append(path)
        return found

    def detect(self) -> bool:
        return len(self.interpreters) > 0

    def collect(self) -> list[dict[str, str]]:
        results = [] 
        
        helper_code = r"""
import json
try:
    import importlib.metadata as metadata
    dists = [{"name": d.metadata["Name"], "version": d.version} for d in metadata.distributions()]
except ImportError:
    import pkg_resources
    dists = [{"name": d.project_name, "version": d.version} for d in pkg_resources.working_set]
print(json.dumps(dists))
"""

        for interpreter in self.interpreters:
            try:
                raw_python_version = subprocess.check_output(
                    [interpreter, "--version"],
                    text=True,
                    stderr=subprocess.STDOUT
                ).strip()

                python_version_str = raw_python_version.split()[1] 
                python_version_clean = normalize_version(python_version_str)
                runtime_name = "Python"

                results.append({
                    "name": runtime_name,
                    "version": python_version_clean,
                    "normalized_name": normalize_name(runtime_name),
                    "normalized_version": python_version_clean,
                    "type": "language_runtime"
                })

                output = subprocess.check_output(
                    [interpreter, "-c", helper_code],
                    text=True,
                    stderr=subprocess.STDOUT
                )

                packages = python_parser.pythonParser(output, log)

                for pkg in packages:
                    name = pkg.get("name")
                    version = pkg.get("version")
                    
                    if not name or not version:
                        continue
                        
                    pkg['normalized_name'] = normalize_name(name)
                    pkg['normalized_version'] = normalize_version(version)
                    pkg['type'] = 'python_package'
                    pkg['parent_language_version'] = python_version_clean 
                    results.append(pkg)

            except Exception as e:
                log.error(f"Failed collecting Python Library: {e}", exc_info=True)
                continue

        return results