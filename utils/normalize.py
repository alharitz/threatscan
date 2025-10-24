# utils/normalize.py

import re
from typing import Optional

VERSION_REGEX = re.compile(r"v?([0-9]+(\.[0-9]+){0,3})")

def normalize_name(name: Optional[str]) -> Optional[str]:
    """
    Menormalkan nama software:
    - Mengubah jadi lowercase
    - Menghapus spasi di awal/akhir
    """
    if not name:
        return None
    
    return name.lower().strip()

def normalize_version(version: Optional[str]) -> Optional[str]:
    """
    Mengekstrak nomor versi 'bersih' (Major.Minor.Patch) 
    dari string versi yang kotor.
    
    Contoh:
    - "v1.2.3-beta"  -> "1.2.3"
    - "2.7.18 (main, Oct 15...)" -> "2.7.18"
    - "141.0.7390.77" -> "141.0.7390.77"
    """
    if not version:
        return None

    match = VERSION_REGEX.search(version)
    
    if match:
        return match.group(1)

    return version.strip()