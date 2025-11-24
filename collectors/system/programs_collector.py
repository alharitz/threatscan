# collectors/system/programs_collector.py

from collectors.base_collector import BaseCollector
from collectors.system import programs_parser
from utils.logger import setup_logger
from utils.normalize import normalize_name, normalize_version
import platform
import shutil
import subprocess

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

                        if name and version and not name.startswith("KB") and "Update" not in name:
                            apps.append({"name": name, "version": version})

                    except FileNotFoundError:
                        continue
                    finally:
                        winreg.CloseKey(subkey)

            except FileNotFoundError:
                continue

            except Exception as e:
                log.error(f"Failed collecting registry key {key_path}: {e}", exc_info=False)
                continue

            finally:
                if 'reg_key' in locals():
                    winreg.CloseKey(reg_key)

        return programs_parser.windowsProgramParser(apps, log)
    
    def _collect_linux_programs(self) -> list[dict]:
        # Debian / Ubuntu family
        if shutil.which("dpkg-query"):
            cmd = "dpkg-query -W -f='${Package}\\t${Version}\\n'"
            try:
                output = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
                return programs_parser.linuxPackageParser(output.stdout, log)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                log.error(f"Failed to collect dpkg packages: '{e}", exc_info=True)
                return []

        # RHEL / Fedora / Rocky / AlmaLinux (modern: DNF)
        elif shutil.which("dnf"):
            cmd = "dnf list installed | tail -n +2 | awk '{print $1\"\\t\"$2}'"
            try:
                output = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
                return programs_parser.linuxPackageParser(output.stdout, log)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                log.error(f"Failed to collect dnf packages: '{e}", exc_info=True)
                return []

        # RHEL / CentOS (older systems: YUM)
        elif shutil.which("yum"):
            cmd = "yum list installed | tail -n +2 | awk '{print $1\"\\t\"$2}'"
            try:
                output = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
                return programs_parser.linuxPackageParser(output.stdout, log)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                log.error(f"Failed to collect yum packages: '{e}", exc_info=True)
                return []

        # OpenSUSE family (zypper)
        elif shutil.which("zypper"):
            # OpenSUSE is RPM-based, so we can use rpm directly for reliable parsing
            cmd = "rpm -qa --qf '%{NAME}\\t%{VERSION}-%{RELEASE}\\n'"
            try:
                output = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
                return programs_parser.linuxPackageParser(output.stdout, log)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                log.error(f"Failed to collect zypper packages via rpm: '{e}", exc_info=True)
                return []

        # Generic RPM-based fallback
        elif shutil.which("rpm"):
            cmd = "rpm -qa --qf '%{NAME}\\t%{VERSION}-%{RELEASE}\\n'"
            try:
                output = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
                return programs_parser.linuxPackageParser(output.stdout, log)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                log.error(f"Failed to collect rpm packages: '{e}", exc_info=True)
                return []

        # Arch Linux family
        elif shutil.which("pacman"):
            cmd = 'pacman -Q --qf "%n\\t%v"'
            try:
                output = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
                return programs_parser.linuxPackageParser(output.stdout, log)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                log.error(f"Failed to collect pacman packages: '{e}", exc_info=True)
                return []

        # Alpine Linux family
        elif shutil.which("apk"):
            cmd = "apk info -v"
            try:
                output = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
                lines = output.stdout.splitlines()
                normalized_lines = []
                import re
                pattern = re.compile(r'^(?P<name>.+?)-(?P<version>\d.*)$')
                for ln in lines:
                    ln = ln.strip()
                    if not ln:
                        continue
                    m = pattern.match(ln)
                    if m:
                        name = m.group('name')
                        ver = m.group('version')
                    else:
                        if '-' in ln:
                            idx = ln.rfind('-')
                            name = ln[:idx]
                            ver = ln[idx + 1:]
                        else:
                            name = ln
                            ver = ""
                    normalized_lines.append(f"{name}\t{ver}")
                normalized_output = "\n".join(normalized_lines) + ("\n" if normalized_lines else "")
                return programs_parser.linuxPackageParser(normalized_output, log)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                log.error(f"Failed to collect apk packages: '{e}", exc_info=True)
                return []

        # Unknown / unsupported system
        else:
            log.warning("Could not detect a known package manager (dpkg, dnf, yum, zypper, rpm, pacman, apk).")
            return []



    def _collect_macos_programs(self) -> list[dict]:
        cmd = ["system_profiler", "SPApplicationsDataType", "-json"]
        
        try:
            output = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return programs_parser.macosPackageParser(output.stdout, log)
        
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            log.error(f"Failed to collect macos packages: '{e}", exc_info=True)
            return []

    def collect(self) -> list[dict]:
        system = platform.system()
        raw_programs_list = []

        if system == "Windows":
            raw_programs_list = self._collect_windows_programs()
        elif system == "Linux":
            raw_programs_list = self._collect_linux_programs()
        elif system == "Darwin":
            raw_programs_list = self._collect_macos_programs()
        else:
            log.warning(f"Unsupported OS: {system}")
            return []

        final_results = []
        for program in raw_programs_list:
            name = program.get("name")
            version = program.get("version")

            if not name or not version:
                continue

            # skip node to avoid duplicate with node_version_collector
            if name.lower() in ("node.js", "nodejs") or "node.js" in name.lower():
                continue
            
            final_results.append({
                "name": name,
                "version": version,
                "normalized_name": normalize_name(name),
                "normalized_version": normalize_version(version),
                "type": "application"
            })
        
        return final_results
