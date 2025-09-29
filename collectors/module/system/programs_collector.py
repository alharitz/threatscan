from collectors.module.base_collector import BaseCollector
import winreg
from utils.logger import setup_logger

log = setup_logger()
log = log.getChild("collector")
log = log.getChild("programs")

class ProgramsCollector(BaseCollector):
    def detect(self) -> bool:
        return True

    def collect(self) -> list[dict]:
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
