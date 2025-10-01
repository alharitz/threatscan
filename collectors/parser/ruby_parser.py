def rubyParser(output: str, _) -> list[dict]:
    packages = []

    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("**"):
            continue
    
        if " (" in line:
            name, versions = line.split(" (", 1)
            versions = versions.rstrip(")")
            versions = versions.replace("default: ", "").strip()

            active_version = versions.split(",")[-1].strip()

            packages.append({
                "name": name,
                "version": active_version
            })

    return packages