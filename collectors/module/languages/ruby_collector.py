from collectors.module.base_collector import BaseCollector
from utils.logger import setup_logger
from collectors.parser import ruby_parser
import shutil
import subprocess

log = setup_logger()
log = log.getChild("collector")
log = log.getChild("ruby")

class RubyCollector(BaseCollector):

    def _ruby_gem_path(self):
        try:
            ruby_path = shutil.which("ruby")
            gem_path = shutil.which("gem")

            return ruby_path, gem_path

        except Exception as e:
            log.error(f"Failed collecting Ruby & Gem Path: {e}", exc_info=True)
            return None, None

    def _ruby_gem_version(self):
        ruby_path, gem_path = self._ruby_gem_path()

        try:
            if ruby_path is None:
                return None, None

            raw_ruby_version = subprocess.check_output(
                [ruby_path, "-v"],
                text=True,
                stderr=subprocess.STDOUT
            )

            ruby_version = raw_ruby_version.split()[1].strip()

            if gem_path is None:
                return ruby_version, None

            raw__gem_version = subprocess.check_output(
                [gem_path, "-v"],
                text=True,
                stderr=subprocess.STDOUT
            )

            gem_version = raw__gem_version.strip()

            return ruby_version, gem_version
        
        except Exception as e:
            log.error(f"Failed collecting Ruby & Gem Version: {e}", exc_info=True)
            return None, None

    def detect(self) -> bool:
        return shutil.which("ruby") is not None
    
    def collect(self) -> list[dict]:
        results = []

        ruby_version, gem_version = self._ruby_gem_version()
        _, gem_path = self._ruby_gem_path()
        package_manager = None

        try:
            packages = []
            if gem_path is not None:
                package_manager = "gem"
                
                output = subprocess.check_output(
                    [gem_path, "list", "--local", "--no-details"],
                    text=True,
                    stderr=subprocess.STDOUT
                )

                packages = ruby_parser.rubyParser(output, log)
            else:
                log.info("gem path not found")

            results.append({
                "language": "ruby",
                "language_version": ruby_version,
                "package_manager": package_manager,
                "package_manager_version": gem_version,
                "packages": packages
            })

        except Exception as e:
            log.error(f"Failed collecting Ruby Packages: {e}", exc_info=True)
            return []
            

        return results