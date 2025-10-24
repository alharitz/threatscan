# collectors/languages/php_collector.py

from collectors.base_collector import BaseCollector
from utils.logger import setup_logger
from collectors.languages import php_parser
import shutil
import subprocess
from utils.normalize import normalize_name, normalize_version

log = setup_logger()
log = log.getChild("collector")
log = log.getChild("php")

class PHPCollector(BaseCollector):
    def detect(self) -> bool:
        return shutil.which("php") is not None
    
    def collect(self) -> list[dict]:
        results = []
        
        php_path = shutil.which("php")
        if php_path is None:
            return []

        php_version_str = "unknown"
        try:
            raw_php_version = subprocess.check_output(
                [php_path, "-v"], text=True, stderr=subprocess.STDOUT
            ).splitlines()[0]
            
            php_version_str = raw_php_version

        except Exception as e:
            log.error(f"Failed collecting PHP Version: {e}", exc_info=True)

        php_name = "PHP"
        php_version_clean = normalize_version(php_version_str)
        
        results.append({
            "name": php_name,
            "version": php_version_clean,
            "normalized_name": normalize_name(php_name),
            "normalized_version": php_version_clean,
            "type": "language_runtime"
        })

        composer_path = shutil.which("composer")
        if composer_path is None:
            log.warning("PHP found, but Composer not found. Skipping package collection.")
            return results

        composer_version_str = "unknown"
        try:
            raw_composer_version = subprocess.check_output(
                [composer_path, "--version"], text=True, stderr=subprocess.STDOUT
            ).splitlines()[0]
            
            composer_version_str = raw_composer_version
            
        except Exception as e:
            log.error(f"Failed collecting Composer Version: {e}", exc_info=True)

        composer_name = "Composer"
        composer_version_clean = normalize_version(composer_version_str)

        results.append({
            "name": composer_name,
            "version": composer_version_clean,
            "normalized_name": normalize_name(composer_name),
            "normalized_version": composer_version_clean,
            "type": "package_manager"
        })

        try:
            output = subprocess.check_output(
                [composer_path, "global", "show", "--format=json"],
                text=True,
                stderr=subprocess.STDOUT
            )
            
            parsed_packages = php_parser.phpParser(output, log)

            for pkg in parsed_packages:
                name = pkg.get("name")
                version = pkg.get("version")
                
                pkg['normalized_name'] = normalize_name(name)
                pkg['normalized_version'] = normalize_version(version)
                pkg['type'] = 'php_package'
                pkg['parent_language_version'] = php_version_clean
                results.append(pkg)

        except Exception as e:
            log.error(f"Failed collecting PHP (Composer) Packages: {e}", exc_info=True)

        return results