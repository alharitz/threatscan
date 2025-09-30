from collectors.module.base_collector import BaseCollector
from utils.logger import setup_logger
import subprocess
import shutil
import json

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
            if path and path not in found:
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

                python_version = raw_python_version.split()[1]

                outputs = subprocess.check_output(
                    [interpreter, "-c", helper_code],
                    text=True,
                    stderr=subprocess.STDOUT
                )

                packages = json.loads(outputs)

                results.append({
                    "language": "python",
                    "language_version": python_version,
                    "packages": packages
                })

            except Exception as e:
                log.error(f"Failed collecting Python Library: {e}", exc_info=True)
                continue

        return results