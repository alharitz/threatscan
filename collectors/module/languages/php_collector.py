from collectors.module.base_collector import BaseCollector
from utils.logger import setup_logger
import shutil
import subprocess
import json

log = setup_logger()
log = log.getChild("collector")
log = log.getChild("php")

class PHPCollector(BaseCollector):
    def _php_composer_path(self):
        try:
            php_path = shutil.which("php")
            composer_path = shutil.which("composer")

            return php_path, composer_path

        except Exception as e:
            log.error(f"Failed collecting PHP & Composer Path: {e}", exc_info=True)
            return None, None

    def _php_composer_version(self):
        php_path, composer_path = self._php_composer_path()

        try:
            if php_path is None:
                return None, None

            raw_php_version = subprocess.check_output(
                    [php_path, "-v"],
                    text=True,
                    stderr=subprocess.STDOUT
                )

            php_first_line = raw_php_version.splitlines()[0]
            php_parts = php_first_line.split()

            if composer_path is None:
                return php_parts, None
                
            raw_composer_version = subprocess.check_output(
                [composer_path, "--version"],
                text=True,
                stderr=subprocess.STDOUT
            )

            composer_first_line = raw_composer_version.splitlines()[0]
            composer_parts = composer_first_line.split()

            return php_parts[1], composer_parts[2]

        except Exception as e:
            log.error(f"Failed collecting PHP & Composer Version: {e}", exc_info=True)
            return None, None

    def detect(self) -> bool:
        return shutil.which("php") is not None
    
    def collect(self) -> list[dict]:
        results = []
        
        php_version, composer_version = self._php_composer_version()
        _, composer_path = self._php_composer_path()
        package_manager = None

        try:
            parsed_packages = []
            if composer_path is not None:
                package_manager = "composer"

                output = subprocess.check_output(
                    [composer_path, "global", "show", "--format=json"],
                    text=True,
                    stderr=subprocess.STDOUT
                )
                
                idx = output.find("{")
                json_output = json.loads(output[idx:])

                packages = json_output.get("installed", [])

                for p in packages:
                    parsed_packages.append({
                        "name": p["name"],
                        "version": p["version"]
                    })
            else:
                log.info("composer not found")

            results.append({
                "language": "php",
                "language_version": php_version,
                "package_manager": package_manager,
                "package_manager_version": composer_version,
                "packages": parsed_packages
            })

            return results

        except Exception as e:
            log.error(f"Failed collecting PHP Packages: {e}", exc_info=True)
            return []