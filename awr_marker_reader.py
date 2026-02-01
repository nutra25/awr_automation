import re
import pythoncom
from win32com.client import dynamic
from awr_udp_span_waiter import open_udp_listener, wait_begin_done_on_socket

def read_marker_all_values(
    *,
    graph_name: str,
    marker_name: str,
    progid: str = "AWR.MWOffice.19.0",
    simulate: bool = True,
    sim_timeout_s: float = 10.0,
    udp_host: str = "127.0.0.1",
    udp_port: int = 50505,
):
    """
    Returns a dict with all parsed marker values + the raw marker text.

    Output example:
    {
      "graph": "it1_load_pull",
      "marker": "m1",
      "raw_text": "...",
      "values": {
         "pload_dbm": 32.705,
         "mag": 0.6865,
         "ang_deg": -126.9,
         "sweepvalue": 2.7050,
         ...
      }
    }

    simulate=True:
      - runs proj.Simulate()
      - waits for BEGIN/DONE UDP signal
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

        # --- find marker by name (case-insensitive) ---
        marker_obj = None
        for i in range(1, int(g.Markers.Count) + 1):
            mi = g.Markers.Item(i)
            if str(getattr(mi, "Name", "")).strip().lower() == marker_name.strip().lower():
                marker_obj = mi
                break
        if marker_obj is None:
            raise RuntimeError(f"Marker bulunamadı: {marker_name} (Graph: {graph_name})")

        txt = marker_obj.DataValueText
        if callable(txt):
            txt = txt()
        txt = "" if txt is None else str(txt)

        values = {}

        # 1) dBm line -> commonly Pload
        m_dbm = re.search(r"([-+]?\d+(?:\.\d+)?)\s*dBm\b", txt, re.IGNORECASE)
        if m_dbm:
            values["pload_dbm"] = float(m_dbm.group(1))

        # 2) Common labels (Mag / Ang / SweepValue etc.)
        # Accept patterns like:
        #   "Mag 0.6865"
        #   "Ang -126.9 Deg"
        #   "SweepValue: 2.70"
        line_pat = re.compile(
            r"^\s*([A-Za-z][A-Za-z0-9_ ]{0,40})\s*[:=]?\s*([-+]?\d+(?:\.\d+)?)\s*([A-Za-z%]+)?\s*$"
        )

        for line in txt.splitlines():
            line = line.strip()
            if not line:
                continue

            mm = line_pat.match(line)
            if not mm:
                continue

            key_raw = mm.group(1).strip().lower().replace(" ", "_")
            num = float(mm.group(2))
            unit = (mm.group(3) or "").strip()

            # normalize a few common keys/units
            if key_raw == "mag":
                values["gamma_mag"] = num
            elif key_raw == "ang":
                # if unit says Deg, store as degrees
                if unit.lower() == "deg":
                    values["gamma_ang_deg"] = num
                else:
                    values["gamma_ang"] = num
            else:
                # store generic
                # if same key repeats, keep last (or make it a list if you prefer)
                values[key_raw] = num

        # 3) Fallback: first numeric in first non-empty line (if nothing else captured for power)
        if "pload_dbm" not in values:
            first_nonempty = next((l.strip() for l in txt.splitlines() if l.strip()), "")
            m_first = re.search(r"([-+]?\d+(?:\.\d+)?)", first_nonempty)
            if m_first:
                values["first_value"] = float(m_first.group(1))

        return {
            "graph": graph_name,
            "marker": marker_name,
            "raw_text": txt,
            "values": values,
        }

    finally:
        pythoncom.CoUninitialize()
