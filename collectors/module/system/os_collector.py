from collectors.module.base_collector import BaseCollector
import platform
import sys

class OSCollector(BaseCollector):

    def detect(self) -> bool:
        return True

    def _collect_windows_info(self) -> tuple[str, str]:
        win_info = platform.win32_ver()
        name = f"Windows{win_info[0]}"
        version = win_info[1]

        return name, version

    def _collect_linux_info(self) -> tuple[str, str]:
        if sys.version_info >= (3, 10):
            try:
                release_data = platform.freedesktop_os_release()
                name = release_data.get('PRETTY_NAME', 'Linux')
                version = release_data.get('VERSION_ID', 'Unknown')

            except OSError:
                name = "Linux"
                version = platform.release()
            
        else:
            try:
                with open("/etc/os-release", "r") as f:
                    release_data = {}
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            value = value.strip('"')
                            release_data[key] = value
                
                name = release_data.get('PRETTY_NAME', 'Linux')
                version = release_data.get('VERSION_ID', 'Unknown')

            except (OSError,ValueError):
                name = "Linux"
                version = platform.release()

        return name, version

    def _collect_macos_info(self) -> tuple[str, str]:
        macos_info = platform.mac_ver()
        name = "macOS"
        version = macos_info[0]

        return name, version

    def collect(self) -> list[dict]:
        os_name, os_version = "Unknwon", "Unknown"

        system = platform.system()

        if system == "Windows":
            os_name, os_version = self._collect_windows_info()
        elif system == "Linux":
            os_name, os_version = self._collect_linux_info()
        elif system == "Darwin":
            os_name, os_version = self._collect_macos_info()


        return [{
            "name": os_name,
            "version": os_version,
        }]
