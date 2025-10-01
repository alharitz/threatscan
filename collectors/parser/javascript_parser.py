def nodeParser(packages: dict, _) -> list[dict]:
        parsed_packages = []

        for pkg_name, pkg_info in packages.items():
            name = pkg_name.lstrip("@").strip()
            version = (pkg_info.get("version") or "").strip() if isinstance(pkg_info, dict) else ""

            parsed_packages.append({
                "name": name,
                "version": version
            })

        return parsed_packages

def bunParser(output: str, _) -> list[dict]:
    lines = output.splitlines()
    packages = []

    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 2 and "@" in parts[-1]:
            name, version = parts[-1].rsplit("@", 1)
            packages.append({"name": name, "version": version})

    return packages