# collectors/languages/javascript_parser.py

def nodeParser(packages: dict, log) -> list[dict]:
    """
    Parses a dictionary of packages (from 'npm list --json').
    Input 'packages' expected to be the 'dependencies' object.
    """
    parsed_packages = []

    for pkg_name, pkg_info in packages.items():
        if not isinstance(pkg_info, dict):
            log.warning(f"Skipping non-dict package entry in nodeParser: {pkg_name}")
            continue

        name = pkg_name.lstrip("@").strip()
        version = (pkg_info.get("version") or "").strip()

        if name and version:
            parsed_packages.append({
                "name": name,
                "version": version
            })

    return parsed_packages

def bunParser(output: str, log) -> list[dict]:
    """
    Parses the raw string output of 'bun pm ls -g'.
    
    Example input lines:
    http-server@14.1.1
    @biomejs/biome@1.8.0
    """
    lines = output.splitlines()
    packages = []

    for line in lines[1:]: 
        line = line.strip()
        
        if not line or "@" not in line:
            continue
            
        try:
            name, version = line.rsplit("@", 1) 
            packages.append({"name": name, "version": version})
            
        except ValueError:
            log.warning(f"Skipping malformed line in bunParser: '{line}'")
            continue

    return packages