# collectors/system/os_parser.py

def parse_os(content: str) -> dict:
    """
    Parses the string content of an /etc/os-release file into a dictionary.
    
    Example input:
    PRETTY_NAME="Ubuntu 22.04.3 LTS"
    NAME="Ubuntu"
    VERSION_ID="22.04"
    """

    release_data = {}

    for line in content.splitlines():
        if '=' in line:
            try:
                key, value = line.strip().split('=', 1)
                value = value.strip('"').strip("'")
                release_data[key] = value
            except ValueError:
                continue
    
    return release_data