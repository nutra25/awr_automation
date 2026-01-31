import pythoncom
from win32com.client import gencache

PROGID = "AWR.MWOffice.19.0"


def _get_ui_name(el):
    for attr in ("Name", "Label"):
        try:
            v = getattr(el, attr)
            v = v() if callable(v) else v
            if v and str(v).strip():
                return str(v).strip()
        except Exception:
            pass
    return ""


def set_element_parameters(
    schematic_name: str,
    *,
    element_index: int | None = None,
    element_id: str | None = None,
    element_name_exact: str | None = None,      # <-- YENİ
    element_name_contains: str | None = None,   # <-- YENİ
    element_has_params: list[str] | None = None,
    params: dict[str, str],
    progid: str = PROGID,
):
    if not params:
        raise ValueError("params boş olamaz")

    pythoncom.CoInitialize()
    try:
        app = gencache.EnsureDispatch(progid)
        prj = app.Project
        sch = prj.Schematics(schematic_name)
        elems = sch.Elements

        target = None
        count = int(elems.Count)

        for i in range(1, count + 1):
            try:
                el = elems(i)
            except Exception:
                el = elems.Item(i)

            # 1) Index (en kesin)
            if element_index is not None and i == element_index:
                target = el
                break

            # 2) UI name exact (PORT1.P1 gibi)
            ui_name = _get_ui_name(el)
            if element_name_exact and ui_name == element_name_exact:
                target = el
                break

            # 3) UI name contains (PORT1 gibi)
            if element_name_contains and element_name_contains in ui_name:
                target = el
                break

            # 4) ID param (VGS, VDS vb.)
            if element_id:
                try:
                    pid = el.Parameters("ID").ValueAsString
                    if pid == element_id:
                        target = el
                        break
                except Exception:
                    pass

            # 5) Param imzası (fallback)
            if element_has_params:
                try:
                    for p in element_has_params:
                        el.Parameters(p)
                    target = el
                    break
                except Exception:
                    pass

        if target is None:
            raise RuntimeError("İstenen element bulunamadı.")

        # Parametreleri set et
        result = {}
        for pname, pval in params.items():
            p = target.Parameters(pname)
            p.ValueAsString = str(pval)
            result[pname] = p.ValueAsString

        return {
            "schematic": schematic_name,
            "element_ui_name": _get_ui_name(target),
            "params_set": result,
        }

    finally:
        pythoncom.CoUninitialize()
