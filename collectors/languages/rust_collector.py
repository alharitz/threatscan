# collectors/languages/rust_collector.py

from collectors.base_collector import BaseCollector
from utils.logger import setup_logger
from collectors.languages import rust_parser
import shutil
import subprocess
from utils.normalize import normalize_name, normalize_version

log = setup_logger()
log = log.getChild("collector")
log = log.getChild("rust")

class RustCollector(BaseCollector):
    def detect(self) -> bool:
        return shutil.which("rustc") is not None
    
    def collect(self) -> list[dict]:
        results = []

        rustc_path = shutil.which("rustc")
        if rustc_path is None:
            return []

        rustc_version_str = "unknown"
        try:
            raw_rustc_version = subprocess.check_output(
                [rustc_path, "--version"], text=True, stderr=subprocess.STDOUT
            ).splitlines()[0] 

            rustc_version_str = raw_rustc_version

        except Exception as e:
            log.error(f"Failed collecting Rustc Version: {e}", exc_info=True)

        runtime_name = "Rust"
        rustc_version_clean = normalize_version(rustc_version_str)
        
        results.append({
            "name": runtime_name,
            "version": rustc_version_clean,
            "normalized_name": normalize_name(runtime_name),
            "normalized_version": rustc_version_clean,
            "type": "language_runtime"
        })

        cargo_path = shutil.which("cargo")
        if cargo_path is None:
            log.warning("Rustc found, but Cargo not found. Skipping package collection.")
            return results 

        cargo_version_str = "unknown"
        try:
            raw_cargo_version = subprocess.check_output(
                [cargo_path, "--version"], text=True, stderr=subprocess.STDOUT
            ).splitlines()[0]
            
            cargo_version_str = raw_cargo_version
            
        except Exception as e:
            log.error(f"Failed collecting Cargo Version: {e}", exc_info=True)

        gem_name = "Cargo"
        cargo_version_clean = normalize_version(cargo_version_str)

        results.append({
            "name": gem_name,
            "version": cargo_version_clean,
            "normalized_name": normalize_name(gem_name),
            "normalized_version": cargo_version_clean,
            "type": "package_manager"
        })

        try:
            output = subprocess.check_output(
                [cargo_path, "install", "--list"],
                text=True,
                stderr=subprocess.STDOUT
            )
            
            parsed_packages = rust_parser.rustParser(output, log)

            for pkg in parsed_packages:
                name = pkg.get("name")
                version = pkg.get("version")
                
                pkg['normalized_name'] = normalize_name(name)
                pkg['normalized_version'] = normalize_version(version)
                pkg['type'] = 'rust_package'
                pkg['parent_language_version'] = rustc_version_clean
                results.append(pkg)

        except Exception as e:
            log.error(f"Failed collecting Rust (Cargo) Packages: {e}", exc_info=True)

        return results