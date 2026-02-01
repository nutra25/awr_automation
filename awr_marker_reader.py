import pythoncom
from win32com.client import dynamic
from awr_udp_span_waiter import open_udp_listener, wait_begin_done_on_socket

def read_marker_raw_text(
    *,
    graph_name: str,
    marker_name: str,
    progid: str = "AWR.MWOffice.19.0",
    simulate: bool = True,
    sim_timeout_s: float = 10.0,
    udp_host: str = "127.0.0.1",
    udp_port: int = 50505,
) -> str:
    """
    Returns the marker's DataValueText as a raw string (no parsing).
    If simulate=True, runs Simulate() and waits for BEGIN/DONE UDP.
    """
    pythoncom.CoInitialize()
    try:
        app = dynamic.Dispatch(progid)
        proj = app.Project

        if simulate:
            sock = open_udp_listener(host=udp_host, port=udp_port)
            try:
                proj.Simulate()
                ok, span = wait_begin_done_on_socket(sock, timeout_s=sim_timeout_s)
                if not ok:
                    raise TimeoutError(f"BEGIN/DONE UDP gelmedi: {span}")
            finally:
                sock.close()

        g = proj.Graphs.Item(graph_name)

        marker_obj = None
        target = marker_name.strip().lower()
        for i in range(1, int(g.Markers.Count) + 1):
            mi = g.Markers.Item(i)
            if str(getattr(mi, "Name", "")).strip().lower() == target:
                marker_obj = mi
                break

        if marker_obj is None:
            raise RuntimeError(f"Marker bulunamadı: {marker_name} (Graph: {graph_name})")

        txt = marker_obj.DataValueText
        if callable(txt):
            txt = txt()

        return "" if txt is None else str(txt)

    finally:
        pythoncom.CoUninitialize()
