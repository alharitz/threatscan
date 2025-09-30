from collectors.module.base_collector import BaseCollector
from utils.logger import setup_logger
import psutil
import socket

log = setup_logger()
log = log.getChild("collector")
log = log.getChild("process")


class ProcessCollector(BaseCollector):
    def detect(self) -> bool:
        return True

    def collect(self) -> list[dict]:
        results = []

        for proc in psutil.process_iter(attrs=["pid", "name", "exe", "cmdline"]):
            try:
                pid = proc.info["pid"]
                ports = []

                for conn in psutil.net_connections(kind="inet"):
                    if conn.pid != pid:
                        continue

                    port = None
                    ip = ""
                    service = "unknown"

                    if conn.laddr:
                        if hasattr(conn.laddr, "port"):
                            port = conn.laddr.port
                            ip = getattr(conn.laddr, "ip", "")
                        elif isinstance(conn.laddr, tuple) and len(conn.laddr) >= 2:
                            port = conn.laddr[1]
                            ip = conn.laddr[0] if len(conn.laddr) >= 1 else ""

                    if port:
                        try:
                            proto = "udp" if getattr(conn, "type", None) == socket.SOCK_DGRAM else "tcp"
                            service = socket.getservbyport(port, proto)
                        except Exception:
                            service = "unknown"

                    ports.append({
                        "ip": ip or "",
                        "port": port or "",
                        "service": service,
                        "status": getattr(conn, "status", "")
                    })

                results.append({
                    "pid": pid,
                    "name": proc.info.get("name"),
                    "exe": proc.info.get("exe"),
                    "cmdline": proc.info.get("cmdline"),
                    "ports": ports
                })
            except Exception:
                continue

        return results



