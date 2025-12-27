# collectors/system/os_collector.py

from os import name
import platform
import sys
from collectors.base_collector import BaseCollector
from utils.normalize import normalize_version, normalize_name
from .os_parser import parse_os
import winreg
from utils.logger import setup_logger

log = setup_logger()
class OSCollector(BaseCollector):

    def detect(self) -> bool:
        return True

    def _collect_windows_info(self) -> dict:
        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"

        info = {
            "name": "Windows (Unknown)",
            "version": "Unknown",
            "full_version": "0.0.0.0",
            "major_build": 0,
            "ubr": 0
        }

        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                info["name"] = winreg.QueryValueEx(key, "ProductName")[0]
                info["major_build"] = int(winreg.QueryValueEx(key, "CurrentBuild")[0])
                info["ubr"] = int(winreg.QueryValueEx(key, "UBR")[0])
                info["full_version"] = f"10.0.{info['major_build']}.{info['ubr']}"

                try:
                    info["version"] = winreg.QueryValueEx(key, "DisplayVersion")[0]
                except FileNotFoundError:
                    info["version"] = winreg.QueryValueEx(key, "ReleaseId")[0]
        except Exception as e:
            log.error(f"Failed to collect Windows OS info: {e}")
            pass

        return info

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
        # name = "macOS"
        version = macos_info[0]

        return name, version

    def collect(self) -> list[dict]:
        system = platform.system()

        display_name = "Unknown"
        display_version = "Unknown" 
        normalized_version = "0.0.0"
        scan_metadata = {}

        scan_metadata = {}
        
        if system == "Windows":
            win_info = self._collect_windows_info()
             
            display_name = win_info["name"]
            display_version = win_info["version"]
            normalized_version = win_info["full_version"]
             
            scan_metadata = {
                 "major_build": win_info["major_build"],
                 "ubr": win_info["ubr"],
                 "family": "windows"
            }

        elif system == "Linux":
             # self._collect_linux_info() (Future implementation)
             pass
        elif system == "Darwin":
             # self._collect_macos_info() (Future implementation)
             pass

        normalized_name = normalize_name(display_name)
        normalized_version = normalize_version(normalized_version)

        return [{
            "name": display_name,
            "version": display_version,
            "normalized_name": normalized_name,
            "normalized_version": normalized_version,
            "type": "operating_system",
            "metadata": scan_metadata 
        }]