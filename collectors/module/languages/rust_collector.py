from collectors.module.base_collector import BaseCollector
from utils.logger import setup_logger
import shutil
import subprocess

log = setup_logger()
log = log.getChild("collector")
log = log.getChild("rust")

class RustCollector(BaseCollector):

    def _rust_cargo_path(self):
        try:
            rustc_path = shutil.which("rustc")
            cargo_path = shutil.which("cargo")

            return rustc_path, cargo_path

        except Exception as e:
            log.error(f"Failed collecting Rust & Cargo Path: {e}", exc_info=True)
            return None, None


    def _rust_cargo_version(self):
        rustc_path, cargo_path = self._rust_cargo_path()

        try:
            if rustc_path is None:
                return None, None
            
            raw_rustc_version = subprocess.check_output(
                [rustc_path, "--version"],
                text=True,
                stderr=subprocess.STDOUT
            )

            rustc_version = raw_rustc_version.split()[1].strip()

            if cargo_path is None:
                return rustc_version, None

            raw_cargo_version = subprocess.check_output(
                [cargo_path, "--version"],
                text=True,
                stderr=subprocess.STDOUT
            )

            cargo_version = raw_cargo_version.split()[1].strip()

            return rustc_version, cargo_version

        except Exception as e:
            log.error(f"Failed collecting Rust & Cargo Version: {e}", exc_info=True)
            return None, None

    def detect(self) -> bool:
        return shutil.which("rustc") is not None
    
    def collect(self) -> list[dict]:
        results = []

        rustc_version, cargo_version = self._rust_cargo_version()
        _, cargo_path = self._rust_cargo_path()
        package_manager = None

        try:
            packages = []
            if cargo_path is not None:
                package_manager = "cargo"

                output = subprocess.check_output(
                    [cargo_path, "install", "--list"],
                    text=True,
                    stderr=subprocess.STDOUT
                )

                for line in output.splitlines():
                    line = line.strip()

                    if not line or ":" not in line:
                        continue
                    
                    name, version = line.split(" v", 1)
                    version = version.split(":")[0].strip()

                    packages.append({
                        "name": name,
                        "version": version
                    })

            else:
                log.error("Failed collecting Rust & Cargo Path")

            results.append({
                "language": "rust",
                "language_version": rustc_version,
                "package_manager": package_manager,
                "package_manager_version": cargo_version,
                "packages": packages
            })

            return results

        except Exception as e:
            log.error(f"Failed collecting Rust & Cargo Packages: {e}", exc_info=True)
            return []