import subprocess
import platform
import os
import re

def run_command(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()
def get_os_info():
    if platform.system() == "Windows":
        result = run_command("wmic os get Caption,Version")
        return result
    else:
        return run_command("cat /etc/os-release")
    
def get_installed_apps():
    if platform.system() == "Windows":
        return run_command("wmic product get name,version")
    else:
        return run_command("dpkg -l")

def get_services():
    if platform.system() == "Windows":
        return run_command("sc query")
    else :
        return run_command("systemctl list-units --type-service --state=running")

def get_open_ports():
    if platform.system() == "Windows":
        return run_command("netstat -ano")
    else:
        return run_command("ss -tuln")

def get_python2_packages():
    python2_packages = run_command("python2 -m pip list")

    if python2_packages == None:
        python2_packages = "Python 2 is not installed"
    return python2_packages

def get_python3_packages():
    python3_packages = run_command("python3 -m pip list")

    if python3_packages == None:
        python3_packages = "Python 3 is not installed"
    return python3_packages

def get_npm_packages():
    npm_packages = run_command("npm list -g --depth=0")
    if npm_packages == None:
        npm_packages = "NPM is not installed"
    return npm_packages

def get_node_version_windows():
    node_version = run_command("node -v")
    if node_version == None:
        node_version = "Node is not installed"
    return node_version
    # version_pattern = re.compile(r'v(\d+\.\d+\.\d+)')
    
    # # Method 1: Try direct execution (if in PATH)
    # try:
    #     result = subprocess.check_output(
    #         ['node', '--version'],
    #         stderr=subprocess.STDOUT,
    #         shell=True,
    #         text=True
    #     )
    #     match = version_pattern.search(result)
    #     if match:
    #         return match.group(1)
    # except (subprocess.CalledProcessError, FileNotFoundError):
    #     pass

def run_scan():
    return{
        # "os_raw":get_os_info(),
        # "installed_apps_raw":get_installed_apps(),
        # "services_raw":get_services(),
        # "open_ports_raw":get_open_ports(),
        # "python2_packages_raw":get_python2_packages(),
        # "python3_packages_raw":get_python3_packages(),
        # "npm_packages_raw":get_npm_packages(),
        # "platform": platform.system(),
        "node_version_raw": get_node_version_windows(),
    }
