import re
import time
import pythoncom
from win32com.client import dynamic
from awr_udp_span_waiter import open_udp_listener, wait_begin_done_on_socket

def _normalize_mode(mode: str) -> str:
    m = str(mode).strip().upper()
    if m not in ("LP", "SP"):
        raise ValueError("mode sadece 'LP' veya 'SP' olmalı.")
    return m

def _default_graph_name(iter_no: int, mode: str) -> str:
    mode = _normalize_mode(mode)
    return f"it{iter_no}_load_pull" if mode == "LP" else f"it{iter_no}_source_pull"

def read_m1_values(iter_no: int,
                   mode: str,
                   marker_name: str = "m1",
                   graph_name: str | None = None,
                   progid: str = "AWR.MWOffice.19.0",
                   simulate: bool = True,
                   sim_timeout_s: float = 10.0,
                   udp_host: str = "127.0.0.1",
                   udp_port: int = 50505):
    """
    Dönen: (pload_dbm, gamma_mag, gamma_ang_deg)

    simulate=True ise:
      - proj.Simulate()
      - Project_AfterSimulate macro'sunun yolladığı UDP sinyalini bekler
    """
    pythoncom.CoInitialize()
    try:
        app = dynamic.Dispatch(progid)
        proj = app.Project
        gname = graph_name or _default_graph_name(iter_no, mode)

        if simulate:
            # 0) ÖNCE dinleyiciyi hazırla (BEGIN'i kaçırma!)
            sock = open_udp_listener(host=udp_host, port=udp_port)
            try:
                # 1) sim'i başlat
                proj.Simulate()

                # 2) BEGIN + DONE bekle
                ok, span = wait_begin_done_on_socket(sock, timeout_s=sim_timeout_s)
                if not ok:
                    raise TimeoutError(f"BEGIN/DONE UDP gelmedi: {span}")
            finally:
                sock.close()

        # --- Marker oku ---
        g = proj.Graphs.Item(gname)

        m = None
        for i in range(1, int(g.Markers.Count) + 1):
            mi = g.Markers.Item(i)
            if str(getattr(mi, "Name", "")).strip().lower() == marker_name.lower():
                m = mi
                break
        if m is None:
            raise RuntimeError(f"Marker bulunamadı: {marker_name} (Graph: {gname})")

        txt = m.DataValueText
        if callable(txt):
            txt = txt()

        # 1) Pload
        m_dbm = re.search(r"([-+]?\d+(?:\.\d+)?)\s*dBm\b", txt, re.IGNORECASE)
        if m_dbm:
            pload_dbm = float(m_dbm.group(1))
        else:
            first_line = txt.strip().splitlines()[0] if txt.strip() else ""
            m_first = re.search(r"([-+]?\d+(?:\.\d+)?)", first_line)
            if not m_first:
                raise RuntimeError(
                    "Pload değeri bulunamadı (ne dBm var ne ilk satır sayısı).\n"
                    f"Graph: {gname}, Marker: {marker_name}\n---\n{txt}\n---"
                )
            pload_dbm = float(m_first.group(1))

        # 2) Mag & Ang
        m_mag = re.search(r"Mag\s*([-+]?\d+(?:\.\d+)?)", txt, re.IGNORECASE)
        m_ang = re.search(r"Ang\s*([-+]?\d+(?:\.\d+)?)\s*Deg", txt, re.IGNORECASE)

        if not (m_mag and m_ang):
            raise RuntimeError(
                "Marker DataValueText içinde Mag/Ang bulunamadı.\n"
                f"Graph: {gname}, Marker: {marker_name}\n---\n{txt}\n---"
            )

        gamma_mag = float(m_mag.group(1))
        gamma_ang_deg = float(m_ang.group(1))

        return pload_dbm, gamma_mag, gamma_ang_deg

    finally:
        pythoncom.CoUninitialize()
