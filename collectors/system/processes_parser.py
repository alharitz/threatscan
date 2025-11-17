# collectors/system/processes_parser.py
import socket
from utils.normalize import normalize_name 

def _get_service_name(port: int, proto: str, log) -> str:
    """Helper kecil buat nebak nama service dari port."""
    try:
        return socket.getservbyport(port, proto)
    except Exception:
        return "unknown"

def _extract_laddr(laddr) -> tuple:
    """Helper buat nge-parse laddr yang formatnya beda-beda."""
    port = None
    ip = ""
    if hasattr(laddr, "port"):
        port = laddr.port
        ip = getattr(laddr, "ip", "")
    elif isinstance(laddr, tuple) and len(laddr) >= 2:
        port = laddr[1]
        ip = laddr[0] if len(laddr) >= 1 else ""
    return port, ip

def parse_services(raw_procs: list[dict], raw_conns: list, log) -> list[dict]:
    """
    Memproses data mentah dari psutil untuk menemukan service/aplikasi
    yang sedang listening di port.
    """
    final_results = []

    # --- 1. Bikin map koneksi DULU (Ini kuncinya) ---
    conn_map = {} # <-- Nama variabelnya 'conn_map'
    for conn in raw_conns:
        # 'conn' adalah object 'sconn'
        if conn.status != 'LISTEN' or not conn.pid:
            continue

        if conn.pid not in conn_map:
            conn_map[conn.pid] = []
        conn_map[conn.pid].append(conn)

    # --- 2. Loop prosesnya CUKUP SEKALI ---
    for proc in raw_procs:
        pid = proc.get("pid")

        # Cek ke 'conn_map', BUKAN 'conn.map' (INI FIX-NYA!)
        if not pid or pid not in conn_map:
            continue

        proc_name = proc.get("name")
        if not proc_name:
            continue

        # Cek ke 'conn_map' lagi
        for conn in conn_map[pid]:
            port, ip = _extract_laddr(conn.laddr)
            if not port:
                continue

            proto = "udp" if getattr(conn, "type", None) == socket.SOCK_DGRAM else "tcp"
            service_guess = _get_service_name(port, proto, log)

            final_results.append({
                "name": proc_name,
                "version": "unknown",
                "normalized_name": normalize_name(proc_name),
                "normalized_version": "unknown",
                "type": "service",
                "port": port,
                "ip_listen": ip or "0.0.0.0",
                "service_guess": service_guess,
                "protocol": proto,
                "pid": pid,
                "exe_path": proc.get("exe")
            })

    return final_results