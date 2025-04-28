import re
import json
import datetime

def parse_os_info(raw_text, platform_type):
    if platform_type == "Windows":
        lines = [line for line in raw_text.split('\n') if line.strip()]
        if len(lines) >= 2:
            headers = [h.strip() for h in re.split(r'\s{2,}', lines[0].strip())]
            values = [v.strip() for v in re.split(r'\s{2,}', lines[1].strip())]

            result = {}
            for i in range(min(len(headers), len(values))):
                result[headers[i]] = values[i]
            return json.dumps(result, indent=4)
    return {"raw": raw_text}

def parse_installed_apps(raw_text, platform_type):
    apps = []
    if platform_type == "Windows":
        lines = raw_text.strip().split("\n")
        if len(lines) >= 2:
            headers = [h.strip() for h in re.split(r'\s{2,}', lines[0].strip())]
            for line in lines[1:]:
                if line.strip():
                    values = [v.strip() for v in re.split(r'\s{2,}', line.strip(), maxsplit=len(headers))]
                    if len(values) == len(headers):
                        row = dict(zip(headers, values))
                        apps.append({k.lower(): v for k, v in row.items()})
    return json.dumps(apps, indent=4)

def parse_services(raw_text, platform_type):
    services = []
    if platform_type == "Windows":
        service_blocks = raw_text.split('\n\n')
        for block in service_blocks:
            if not block.strip():
                continue

            service = {}
            for line in block.split('\n'):
                line = line.strip()
                if line.startswith('SERVICE_NAME:'):
                    service['name'] = line.replace('SERVICE_NAME:', '').strip()
                elif line.startswith('DISPLAY_NAME:'):
                    service['display_name'] = line.replace('DISPLAY_NAME:', '').strip()
                elif line.startswith('STATE') and 'RUNNING' in line:
                    service['state'] = 'RUNNING'

            if service and 'name' in service and 'state' in service:
                services.append(service)
    return json.dumps(services, indent=4)

def parse_open_ports (raw_text, platform_type):
    ports = []
    if platform_type == "Windows":
        lines = raw_text.strip().split('\n')
        headers = None
        for line in lines:
            line = line.strip()
            if 'Proto' in line and 'Local Address' in line:
                headers = [h.strip() for h in re.split(r'\s{2,}', line)]
            elif line and headers and 'LISTENING' in line:
                values = [v.strip() for v in re.split(r'\s{2,}', line.strip(), maxsplit=len(headers))]
                if len(values) >= len(headers):
                    port_info = dict(zip(headers, values))
                    ports.append(port_info)

    return json.dumps(ports, indent=4)

def parse_python_packages(raw_text, version):
    packages = []
    if raw_text and "Package" in raw_text and "Version" in raw_text:
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

        start_idx = 0
        for i, line in enumerate(lines):
            if "Package" in line and "Version" in line:
                start_idx = i + 1
                break
        
        for i in range(start_idx, len(lines)):
            parts = re.split(r'\s{2,}', lines[i].strip())
            if len(parts) >= 2:
                packages.append({
                    "name": parts[0],
                    "version": parts[1]
                })
    elif "not installed" in raw_text:
        return f"Python {version} is not installed"
    
    return json.dumps(packages, indent=4)

def parse_npm_packages(raw_text):
    packages = []
    
    if raw_text is None or "not installed" in raw_text.lower():
        return "NPM is not installed"
    
    lines = raw_text.split('\n')
    if len(lines) <= 1:
        return json.dumps({"packages": []}, indent=4)
    
    for line in lines[1:]:
        line = line.strip()
        
        if "@" in line:
            parts = line.rsplit('@', 1)
            if len(parts) == 2:
                name = parts[0].strip()
                name = re.sub(r'^[^a-zA-Z0-9@_-]+', '', name)
                
                packages.append({
                    "name": name,
                    "version": parts[1].strip()
                })
    
    return json.dumps(packages, indent=4)  

def parse_node_version(version):
    packages = []
    
    clean_version = version.removeprefix('v')
    packages.append({
        "name": "node",
        "version": clean_version
    })
    
    return json.dumps(packages, indent=4)

def parse_scan_results(raw_results):
    """Main function to parse all scan results"""
    platform_type = raw_results.get("platform", "")
    
    parsed_results = {
        "os": parse_os_info(raw_results.get("os_raw", ""), platform_type),
        "installed_apps": parse_installed_apps(raw_results.get("installed_apps_raw", ""), platform_type),
        "services": parse_services(raw_results.get("services_raw", ""), platform_type),
        "open_ports": parse_open_ports(raw_results.get("open_ports_raw", ""), platform_type),
        "python2_packages": parse_python_packages(raw_results.get("python2_packages_raw", ""), "2"),
        "python3_packages": parse_python_packages(raw_results.get("python3_packages_raw", ""), "3"),
        "npm_packages": parse_npm_packages(raw_results.get("npm_packages_raw", "")),
        "node_version": parse_node_version(raw_results.get("node_version_raw")),
        "date_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    return parsed_results