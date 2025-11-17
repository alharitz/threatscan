# collectors/system/programs_parser.py

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
    
def windowsProgramParser(raw_apps: list[dict], log) -> list[dict]:
    """
    Deduplicates a list of installed applications collected from 
    different registry hives.
    """
    try:
        # Pake logic deduplikasi kamu yang udah pinter!
        apps_tuples = [tuple(sorted(app.items())) for app in raw_apps]
        unique_apps_tuples = list(set(apps_tuples))
        results = [dict(unique_app_tuple) for unique_app_tuple in unique_apps_tuples]
        return results
    except Exception as e:
        log.error(f"Failed to deduplicate windows programs: {e}")
        return []