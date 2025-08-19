import subprocess
import platform
import json
import threading
from core.parser import (
    parse_os_info,
    parse_installed_apps,
    parse_services,
    parse_open_ports,
    parse_python_packages,
    parse_npm_packages,
    parse_node_version,
)


total_data = {"total": 0, "completed": 0, "data": {}}

data_lock = threading.Lock()
stop_event = threading.Event()


def update_progress():
    with data_lock:
        total_data["completed"] += 1


def run_command(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            return ""  # Return empty string instead of None
        return result.stdout.strip()
    except Exception as e:
        print(f"Command execution error: {str(e)}")
        return ""  # Return empty string on error


def get_os_info():
    if platform.system() == "Windows":
        result = run_command("wmic os get Caption,Version")
        with data_lock:
            total_data["data"]["os"] = parse_os_info(result, platform.system())
        update_progress()


def get_installed_apps():
    if platform.system() == "Windows":
        ps_command = r"Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*, HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\* | Select-Object DisplayName, DisplayVersion | ConvertTo-Json"
        result = subprocess.run(
            ["powershell", "-Command", ps_command], capture_output=True, text=True
        )
        datas = json.loads(result.stdout.strip())
        clean_data = [data for data in datas if data.get("DisplayName")]
        with data_lock:
            total_data["data"]["installed_apps"] = clean_data
        update_progress()


def get_python2_packages():
    if platform.system() == "Windows":
        python2_packages = run_command("python2 -m pip list")
        if python2_packages is None:
            python2_packages = "Python 2 is not installed"
        with data_lock:
            total_data["data"]["python2_packages"] = parse_python_packages(
                python2_packages, "2"
            )
        update_progress()


def get_python3_packages():
    if platform.system() == "Windows":
        python3_packages = run_command("python3 -m pip list")
        if python3_packages is None:
            python3_packages = "Python 3 is not installed"
        with data_lock:
            total_data["data"]["python3_packages"] = parse_python_packages(
                python3_packages, "3"
            )
        update_progress()


def get_npm_packages():
    if platform.system() == "Windows":
        npm_packages = run_command("npm list -g --depth=0")
        if npm_packages is None:
            npm_packages = "NPM is not installed"
        with data_lock:
            total_data["data"]["npm_packages"] = parse_npm_packages(npm_packages)
        update_progress()


def get_node_version_windows():
    if platform.system() == "Windows":
        node_version = run_command("node -v")
        if node_version is None:
            node_version = "Node is not installed"
        with data_lock:
            total_data["data"]["node_version"] = parse_node_version(node_version)
        update_progress()


# def get_services():
#     if platform.system() == "Windows":
#         result = run_command("sc query")
#         with data_lock:
#             total_data["data"]["services"] = parser.parse_services(result, platform.system())
#         update_progress()
#     else:
#         result = run_command("systemctl list-units --type-service --state=running")
#         with data_lock:
#             total_data["data"]["services"] = parser.parse_services(result)
#         update_progress()

# def get_open_ports():
#     if platform.system() == "Windows":
#         result = run_command("netstat -ano")
#         with data_lock:
#             total_data["data"]["open_ports"] = parser.parse_open_ports(result, platform.system())
#         update_progress()
#     else:
#         result = run_command("ss -tuln")
#         with data_lock:
#             total_data["data"]["open_ports"] = parser.parse_open_ports(result)
#         update_progress()

scan_functions = [
    get_os_info,
    get_installed_apps,
    # get_services,
    # get_open_ports,
    get_python2_packages,
    get_python3_packages,
    get_npm_packages,
    get_node_version_windows,
]


def run_scan():
    try:
        with data_lock:
            total_data["total"] = len(scan_functions)
            total_data["completed"] = 0
            total_data["data"] = {}

        threads = []
        for func in scan_functions:
            thread = threading.Thread(target=func, daemon=True)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        return total_data
    except KeyboardInterrupt:
        print("\n⛔ Stopping scan...")
        stop_event.set()
        return total_data
