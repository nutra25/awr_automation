# awr_udp_span_waiter.py
import socket
import time

def wait_udp_msg(sock: socket.socket, prefix: str, timeout_s: float):
    sock.settimeout(timeout_s)
    t0 = time.time()
    while True:
        left = timeout_s - (time.time() - t0)
        if left <= 0:
            return False, {"timeout_s": timeout_s, "prefix": prefix}

        sock.settimeout(left)
        data, addr = sock.recvfrom(4096)
        msg = data.decode("utf-8", errors="ignore").strip()
        if msg.startswith(prefix):
            return True, {"from": addr, "msg": msg}

def wait_begin_done_on_socket(sock: socket.socket, timeout_s: float = 1800.0):
    ok1, info1 = wait_udp_msg(sock, "PY_SIM_BEGIN|", timeout_s)
    if not ok1:
        return False, {"stage": "begin", **info1}

    ok2, info2 = wait_udp_msg(sock, "PY_SIM_DONE|", timeout_s)
    if not ok2:
        return False, {"stage": "done", **info2, "begin": info1}

    return True, {"begin": info1, "done": info2}

def open_udp_listener(host: str = "127.0.0.1", port: int = 50505) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # tekrar çalıştırmalarda "Address already in use" görmeyelim
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    return sock
