# utils/normalize.py

import re
from typing import Optional

VERSION_REGEX = re.compile(r"v?([0-9]+(\.[0-9]+){0,3})")

def normalize_name(raw_name: str) -> str:
    """
    Applies aggressive normalization rules to strip common noise and irrelevant details
    from software display names to improve CPE matching accuracy.
    """
    if not raw_name:
        return ""

    # 1. Convert to lowercase and strip leading/trailing spaces
    name = raw_name.lower().strip()

    # 2. Aggressively remove common version patterns and their leading/trailing spaces
    # Matches patterns like ' 6.22', ' v2.7.0', or ' 3.0.0'
    name = re.sub(r'\s*v?\d+(\.\d+){1,4}.*$', '', name)

    # 3. Remove common architecture/platform suffixes
    # Matches patterns like (64-bit), x64, amd64, etc.
    name = re.sub(r'\(.*?\)|\[.*?\]', '', name) # Remove anything in parenthesis/brackets first
    name = re.sub(r'x86|x64|amd64|64-bit|32-bit|msi|vmsi|x64msi', '', name)

    # 4. Remove common display/installer suffixes
    # Patterns like ' release', ' stable', ' installer', ' runtime', ' sdk'
    name = re.sub(r' release| stable| installer| runtime| sdk| with msys2', '', name)

    # 5. Clean up extra spaces, dashes, and periods left over
    name = re.sub(r'\s+', ' ', name) # Replace multiple spaces with a single space
    name = name.strip()
    name = name.replace("-", "").replace(".", "") # Remove remaining common separators

    return name

def normalize_version(raw_version: str) -> str:
    """
    Simple normalization for version strings (strips non-numeric prefixes like 'v' or 'V').
    """
    if not raw_version:
        return ""
    
    # Simple version cleaning: remove non-numeric chars from the start
    version = raw_version.lstrip("vV")
    
    # Special handling for versions that end in metadata (e.g., '2.7.0-1')
    version = version.split('-')[0].strip()
    
    return version