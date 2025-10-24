# collectors/languages/ruby_collector.py

from collectors.base_collector import BaseCollector
from utils.logger import setup_logger
from collectors.languages import ruby_parser
import shutil
import subprocess
from utils.normalize import normalize_name, normalize_version

log = setup_logger()
log = log.getChild("collector")
log = log.getChild("ruby")

class RubyCollector(BaseCollector):

    def detect(self) -> bool:
        return shutil.which("ruby") is not None
    
    def collect(self) -> list[dict]:
        results = []

        ruby_path = shutil.which("ruby")
        if ruby_path is None:
            return []

        ruby_version_str = "unknown"
        try:
            raw_ruby_version = subprocess.check_output(
                [ruby_path, "-v"], text=True, stderr=subprocess.STDOUT
            ).splitlines()[0]
            
            ruby_version_str = raw_ruby_version

        except Exception as e:
            log.error(f"Failed collecting Ruby Version: {e}", exc_info=True)

        runtime_name = "Ruby"
        ruby_version_clean = normalize_version(ruby_version_str)
        
        results.append({
            "name": runtime_name,
            "version": ruby_version_clean,
            "normalized_name": normalize_name(runtime_name),
            "normalized_version": ruby_version_clean,
            "type": "language_runtime"
        })

        gem_path = shutil.which("gem")
        if gem_path is None:
            log.warning("Ruby found, but Gem not found. Skipping package collection.")
            return results

        gem_version_str = "unknown"
        try:
            raw_gem_version = subprocess.check_output(
                [gem_path, "-v"], text=True, stderr=subprocess.STDOUT
            ).strip()
            
            gem_version_str = raw_gem_version
            
        except Exception as e:
            log.error(f"Failed collecting Gem Version: {e}", exc_info=True)

        gem_name = "RubyGems"
        gem_version_clean = normalize_version(gem_version_str)

        results.append({
            "name": gem_name,
            "version": gem_version_clean,
            "normalized_name": normalize_name(gem_name),
            "normalized_version": gem_version_clean,
            "type": "package_manager"
        })

        try:
            output = subprocess.check_output(
                [gem_path, "list", "--local", "--no-details"],
                text=True,
                stderr=subprocess.STDOUT
            )
            
            parsed_packages = ruby_parser.rubyParser(output, log)

            for pkg in parsed_packages:
                name = pkg.get("name")
                version = pkg.get("version")
                
                pkg['normalized_name'] = normalize_name(name)
                pkg['normalized_version'] = normalize_version(version)
                pkg['type'] = 'ruby_package'
                pkg['parent_language_version'] = ruby_version_clean
                results.append(pkg)

        except Exception as e:
            log.error(f"Failed collecting Ruby (Gem) Packages: {e}", exc_info=True)

        return results