# collectors/languages/rust_parser.py

def rustParser(output: str, log) -> list[dict]:
    packages = []

    for line in output.splitlines():
        line = line.strip()

        if not line or " v" not in line or not line.endswith(":"):
            continue
        
        try:
            name, version = line.split(" v", 1)
            version = version.rsplit(":", 1)[0].strip()

            packages.append({
                "name": name.strip(),
                "version": version
            })
        
        except Exception as e:
            log.warning(f"Skipping malformed line in rustParser: '{line}'. Error: {e}")
            continue

    return packages