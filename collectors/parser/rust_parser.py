def rustParser(output: str, _) -> list[dict]:
    packages = []

    for line in output.splitlines():
        line = line.strip()

        if not line or ":" not in line:
            continue
        
        name, version = line.split(" v", 1)
        version = version.split(":")[0].strip()

        packages.append({
            "name": name,
            "version": version
        })

    return packages