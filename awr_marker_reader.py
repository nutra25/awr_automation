import pythoncom
from win32com.client import dynamic

def read_marker_raw_text(
    *,
    graph_name: str,
    marker_name: str,
    progid: str = "AWR.MWOffice.19.0",
    simulate: bool = True
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
            simulator = proj.Simulator
            simulator.Analyze()

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
