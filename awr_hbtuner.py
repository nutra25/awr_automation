import pythoncom
from win32com.client import gencache


def set_tuner_mag_ang(
    schematic_name: str,
    mode: str,
    mag_expr: str,
    ang_expr: str,
    progid: str = "AWR.MWOffice.19.0",
    element_lp: int = 12,
    element_sp: int = 11,
    mag_param: str = "Mag1",
    ang_param: str = "Ang1",
):
    """
    mode = 'LP' -> Elements(12)
    mode = 'SP' -> Elements(11)

    mag_expr / ang_expr: ValueAsString'e yazılacak ifade (örn 'calcMag(50,0,z0)')
    """
    mode_u = str(mode).strip().upper()
    if mode_u not in ("LP", "SP"):
        raise ValueError("mode sadece 'LP' veya 'SP' olmalı.")

    element_idx = element_lp if mode_u == "LP" else element_sp

    pythoncom.CoInitialize()
    try:
        app = gencache.EnsureDispatch(progid)
        prj = app.Project
        sch = prj.Schematics(schematic_name)

        elems = sch.Elements

        # Senin örnekteki gibi direct indexing
        try:
            tuner = elems(element_idx)
        except Exception:
            # Fallback: Item tabanlı erişim
            tuner = elems.Item(element_idx)

        p_mag = tuner.Parameters(mag_param)
        p_ang = tuner.Parameters(ang_param)

        # Set
        p_mag.ValueAsString = mag_expr
        p_ang.ValueAsString = ang_expr

        # Readback
        return {
            "mode": mode_u,
            "schematic": schematic_name,
            "element_index": element_idx,
            "mag_readback": p_mag.ValueAsString,
            "ang_readback": p_ang.ValueAsString,
        }

    finally:
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    # Örnek kullanım:
    out = set_tuner_mag_ang(
        schematic_name="VDS40_Load_Pull",
        mode="LP",
        mag_expr="calcMag(50,0,z0)",
        ang_expr="calcAng(50,0,z0)",
    )
    print("Mag1 readback:", out["mag_readback"])
    print("Ang1 readback:", out["ang_readback"])

    out = set_tuner_mag_ang(
        schematic_name="VDS40_Load_Pull",
        mode="SP",
        mag_expr="calcMag(20,0,z0)",
        ang_expr="calcAng(20,0,z0)",
    )
    print("SP Mag1 readback:", out["mag_readback"])
    print("SP Ang1 readback:", out["ang_readback"])


