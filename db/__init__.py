# /db/__init__.py

""" Database utilities: connection pool, schema init, and CPE injector """

from .connection import get_pool
from .init_db import init_cpe_table
from .cpe_injector import inject_cpe_chunks
# TODO: Add CVE

__all__ = ["get_pool", "init_cpe_table", "inject_cpe_chunks"]