# collectors/system/os_collector.py

import platform
import sys
from collectors.base_collector import BaseCollector
from utils.normalize import normalize_version, normalize_name
from .os_parser import parse_os

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
                    content = f.read()

                release_data = parse_os(content)
                
                name = release_data.get('PRETTY_NAME', 'Linux')
                version = release_data.get('VERSION_ID', 'Unknown')

            except (OSError, ValueError):
                name = "Linux"
                version = platform.release()

        return name, version

    def _collect_macos_info(self) -> tuple[str, str]:
        macos_info = platform.mac_ver()
        name = "macOS"
        version = macos_info[0]

        return name, version

    def collect(self) -> list[dict]:
        os_name, os_version = "Unknown", "Unknown"
        system = platform.system()

        if system == "Windows":
            os_name, os_version = self._collect_windows_info()
        elif system == "Linux":
            os_name, os_version = self._collect_linux_info()
        elif system == "Darwin":
            os_name, os_version = self._collect_macos_info()

        normalized_name = normalize_name(os_name)
        normalized_version = normalize_version(os_version)

        return [{
            "name": os_name,
            "version": os_version,
            "normalized_name": normalized_name,
            "normalized_version": normalized_version,
            "type": "operating_system"
        }]