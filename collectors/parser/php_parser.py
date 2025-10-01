import json

def phpParser(output: str, _) -> list[dict]:
    parsed_packages = []

    idx = output.find("{")
    json_output = json.loads(output[idx:])

    packages = json_output.get("installed", [])

    for p in packages:
        parsed_packages.append({
            "name": p["name"],
            "version": p["version"]
                })

    return parsed_packages