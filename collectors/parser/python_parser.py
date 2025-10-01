import json

def pythonParser(output: str, _) -> list[dict]:
    return json.loads(output)