from collectors.module.base_collector import BaseCollector
from collectors.parser import program_collector_parser
from utils.logger import setup_logger
import platform
import shutil
import subprocess
import json

log = setup_logger()
log = log.getChild("collector")
log = log.getChild("programs")

class ProgramsCollector(BaseCollector):
    def detect(self) -> bool:
        return True

    def _collect_windows_programs(self) -> list[dict]:
        import winreg

        uninstall_keys = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
                ]

        apps = []
        for root, key_path in uninstall_keys:

            try:
                # Open registry for each key
                reg_key = winreg.OpenKey(root, key_path)
                subkey_count = winreg.QueryInfoKey(reg_key)[0]

                for i in range(subkey_count):
                    # Open each subkey
                    subkey_name = winreg.EnumKey(reg_key, i)
                    subkey = winreg.OpenKey(reg_key, subkey_name)

                    try:
                        # Extract name and version
                        name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                        version, _ = winreg.QueryValueEx(subkey, "DisplayVersion")

                        apps.append({"name": name, "version": version})

                    except FileNotFoundError:
                        continue

            except FileNotFoundError:
                continue

            except Exception as e:
                log.error(f"Failed collecting Installed Program: {e}", exc_info=True)
                return []

        apps_tuples = [tuple(sorted(app.items())) for app in apps]
        unique_apps_tuples = list(set(apps_tuples))
        results = [dict(unique_app_tuple) for unique_app_tuple in unique_apps_tuples]

        return results
    
    def _collect_linux_programs(self) -> list[dict]:
        if shutil.which("dpkg-query"):
            cmd = "dpkg-query -W -f='${Package}\\t${Version}\\n'"

            try:
                output = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
                return program_collector_parser.linuxPackageParser(output.stdout, log)

            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                log.error(f"Failed to collect dpkg packages: '{e}", exc_info=True)
                return []

        elif shutil.which("rpm"):
            cmd = "rpm -qa --qf '%{NAME}\\t%{VERSION}-%{RELEASE}\\n'"
            
            try:
                output = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
                return program_collector_parser.linuxPackageParser(output.stdout, log)
            
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                log.error(f"Failed to collect rpm packages: '{e}", exc_info=True)
                return []

        elif shutil.which("pacman"):
            cmd = 'pacman -Q --qf "%n\\t%v"'
            
            try:
                output = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
                return program_collector_parser.linuxPackageParser(output.stdout, log)
            
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                log.error(f"Failed to collect pacman packages: '{e}", exc_info=True)
                return []

        else:
            log.warning("Could not detect a known pacakage manager(dpg, rpm, pacman).")
            return []
            
    def _collect_macos_programs(self) -> list[dict]:
        cmd = ["system_profiler", "SPApplicationsDataType", "-json"]
        
        try:
            output = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return program_collector_parser.macosPackageParser(output.stdout, log)
        
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            log.error(f"Failed to collect macos packages: '{e}", exc_info=True)
            return []

    def collect(self) -> list[dict]:
        system = platform.system()

        if system == "Windows":
            return self._collect_windows_programs()
        elif system == "Linux":
            return self._collect_linux_programs()
        elif system == "Darwin":
            return self._collect_macos_programs()

        log.warning(f"Unsupported OS: {system}")
        return []
