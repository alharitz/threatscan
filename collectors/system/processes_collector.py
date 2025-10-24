# collectors/system/processes_collector.py

from collectors.base_collector import BaseCollector
from utils.logger import setup_logger
import psutil
from . import processes_parser

log = setup_logger()
log = log.getChild("collector")
log = log.getChild("process")

class ProcessCollector(BaseCollector):
    def detect(self) -> bool:
        return True

    def collect(self) -> list[dict]:
        raw_procs = []

        try:
            attrs = ["pid", "name", "exe", "cmdline"]
            raw_procs = [p.info for p in psutil.process_iter(attrs=attrs)]
        except Exception as e:
            log.error(f"Failed to iterate processes: {e}")
            
        raw_conns = []
        try:
            raw_conns = psutil.net_connections(kind="inet")
        except psutil.AccessDenied:
            log.warning("Access denied to get net_connections. Run as Admin/root?")
        except Exception as e:
            log.error(f"Failed to get net_connections: {e}")

        try:
            return processes_parser.parse_services(raw_procs, raw_conns, log)
        except Exception as e:
            log.error(f"Failed during process parsing: {e}", exc_info=True)
            return []