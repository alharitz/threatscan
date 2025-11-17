# collectors/languages/perl_parser.py

def perlParser(output: str, log) -> list[dict]:
    packages = []

    for line in output.splitlines():
        line = line.strip()
        if not line: # Skip baris kosong
            continue

        parts = line.split(maxsplit=1)

        if len(parts) == 2:
            name, version = parts

            if version and version.lower() != 'undef':
                packages.append({
                    "name": name.strip(),
                    "version": version.strip().lstrip("v")
                })
            else:
                log.warning(f"Skipping Perl module with no version: {name}")
        
        elif line:
            log.warning(f"Skipping malformed line in perlParser: '{line}'")

    return packages