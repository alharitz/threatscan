def perlParser(output: str, _) -> list[dict]:
    packages = []

    for line in output.splitlines():
        parts = line.strip().split(maxsplit=1)

        if len(parts) :
            name, version = parts
            version = version.strip("v")

            packages.append({
                "name": name,
                "version": version
            })

    return packages