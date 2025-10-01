import json

def linuxPackageParser(command_output: str, log) -> list[dict]:
    results = []

    for line in command_output.strip().split('\n'):
        if '\t' in line:
            try:
                name, version = line.split('\t')
                results.append({
                    "name": name,
                    "version": version
                })

            except ValueError:
                log.warning(f"Skipping malformed lines: '{line}'")
                continue

    return results

def macosPackageParser(command_output: str, log) -> list[dict]:
    programs = []
    try:
        data = json.loads(command_output)
        application_list = data.get("SPApplicationsDataType", [])

        for app in application_list:
            name = app.get("_name")
            version = app.get("version")
            
            if name and version:
                programs.append({"name": name, "version": version})
        
        return programs

    except json.JSONDecodeError as e:
        log.error(f"Failed to parse system_profiler JSON output: {e}")
        return []