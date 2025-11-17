# collectors/languages/php_parser.py

import json

def phpParser(output: str, log) -> list[dict]:
    parsed_packages = []

    idx = output.find("{")
    
    if idx == -1:
        log.error(f"Failed to find start of JSON in Composer output. Output was: {output[:200]}...")
        return []

    try:
        json_output = json.loads(output[idx:])
        packages = json_output.get("installed", [])

        for p in packages:
            if p.get("name") and p.get("version"):
                parsed_packages.append({
                    "name": p["name"],
                    "version": p["version"]
                })
        
        return parsed_packages
    
    except json.JSONDecodeError as e:
        log.error(f"Failed to parse Composer JSON: {e}")
        return []