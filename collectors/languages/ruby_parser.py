# collectors/languages/ruby_parser.py

def rubyParser(output: str, log) -> list[dict]:
    packages = []

    for line in output.splitlines():
        if not line or line.startswith("**"):
            continue
        
        try:
            if " (" in line:
                name, versions = line.split(" (", 1)
                versions = versions.rstrip(")")
                versions = versions.replace("default: ", "").strip()
                active_version = versions.split(",")[-1].strip()

                if name and active_version:
                    packages.append({
                        "name": name,
                        "version": active_version
                    })
        
        except Exception as e:
            log.warning(f"Skipping malformed line in rubyParser: '{line}'. Error: {e}")
            continue

    return packages