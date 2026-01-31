# pip install pywin32 pywinauto
import time
import threading
from dataclasses import dataclass

import pythoncom
import win32com.client as win32
from pywinauto import Desktop
from pywinauto.keyboard import send_keys


@dataclass
class LoadPullParams:
    angle_deg: str
    center_mag: str
    radius: str


class AwrLoadPullAutomator:
    def __init__(
        self,
        progid: str = "AWR.MWOffice.19.0",
        down_blast: int = 100,
        pause: float = 0.01,
        window_timeout_s: float = 25.0,
    ):
        self.progid = progid
        self.down_blast = down_blast
        self.pause = pause
        self.window_timeout_s = window_timeout_s

    # ---------- Naming helpers ----------
    @staticmethod
    def _normalize_mode(mode: str) -> str:
        m = str(mode).strip().upper()
        if m not in ("LP", "SP"):
            raise ValueError("mode sadece 'LP' veya 'SP' olmalı.")
        return m

    @staticmethod
    def make_wiz_name(iter_no: int, mode: str) -> str:
        mode = AwrLoadPullAutomator._normalize_mode(mode)
        return f"it{iter_no}_{mode}"

    @staticmethod
    def make_loadpull_title(iter_no: int, mode: str) -> str:
        return f"Load Pull - {AwrLoadPullAutomator.make_wiz_name(iter_no, mode)}"

    # ---------- COM: open WizardDoc Edit (async) ----------
    def _open_wizarddoc_edit_async(self, wiz_name: str):
        result = {"error": None}

        def worker():
            pythoncom.CoInitialize()
            try:
                try:
                    app = win32.GetActiveObject(self.progid)
                except Exception:
                    app = win32.gencache.EnsureDispatch(self.progid)

                app.Visible = True
                time.sleep(0.2)

                proj = app.Project
                wiz = None
                for i in range(1, proj.WizardDocs.Count + 1):
                    d = proj.WizardDocs.Item(i)
                    if str(getattr(d, "Name", "")).strip().lower() == wiz_name.lower():
                        wiz = d
                        break
                if wiz is None:
                    raise RuntimeError(f"WizardDoc bulunamadı: {wiz_name}")

                wiz.Edit()

            except Exception as e:
                result["error"] = e
            finally:
                pythoncom.CoUninitialize()

        t = threading.Thread(target=worker, daemon=True)
        t.start()
        return t, result

    # ---------- UI: wait window ----------
    def _wait_loadpull_window(self, title: str):
        t0 = time.time()
        while time.time() - t0 < self.window_timeout_s:
            try:
                dlg = Desktop(backend="win32").window(title=title)
                if dlg.exists():
                    dlg.wait("visible enabled ready", timeout=3)
                    dlg.set_focus()
                    return dlg
            except Exception:
                pass
            time.sleep(0.2)
        raise TimeoutError(f"Pencere bulunamadı: '{title}'")

    # ---------- UI: typing helpers ----------
    @staticmethod
    def _type_value_no_enter(value: str):
        send_keys("^a{BACKSPACE}")
        send_keys(str(value))
        time.sleep(0.05)

    def _fill_custom_gamma_points_and_save(self, params: LoadPullParams):
        """
        Değerleri gir:
        - DOWN blast
        - 2UP + RIGHT
        - angle (no enter) -> UP
        - mag   (no enter) -> UP
        - radius -> ENTER (commit)
        - ENTER (save)
        """
        for _ in range(self.down_blast):
            send_keys("{DOWN}")
            time.sleep(self.pause)

        send_keys("{UP}")
        time.sleep(0.02)
        send_keys("{UP}")
        time.sleep(0.02)
        send_keys("{RIGHT}")
        time.sleep(0.05)

        # Angle
        self._type_value_no_enter(params.angle_deg)
        send_keys("{UP}")
        time.sleep(0.03)
        send_keys("{RIGHT}")
        time.sleep(0.03)

        # Mag
        self._type_value_no_enter(params.center_mag)
        send_keys("{UP}")
        time.sleep(0.03)
        send_keys("{RIGHT}")
        time.sleep(0.03)

        # Radius + ENTER
        self._type_value_no_enter(params.radius)
        send_keys("{ENTER}")
        time.sleep(0.12)

        # Save/OK (senin case'inde ENTER)
        send_keys("{ENTER}")
        time.sleep(0.15)

    @staticmethod
    def _close_with_esc():
        send_keys("{ESC}")
        time.sleep(0.2)

    @staticmethod
    def _run_with_enter():
        """
        Tek ENTER ile run/simulate tetikleniyorsa.
        (Gerekirse bunu ALT+R vs. yaparız)
        """
        send_keys("{ENTER}")
        time.sleep(0.2)

    # ---------- Public API ----------
    def apply(self, iter_no: int, mode: str, params: LoadPullParams, run_after_save: bool = True):
        """
        Akış:
          1) WizardDoc aç
          2) değerleri gir + kaydet
          3) ESC ile kapat
          4) WizardDoc'u tekrar aç
          5) ENTER ile run (opsiyonel)
        """
        wiz_name = self.make_wiz_name(iter_no, mode)
        title = self.make_loadpull_title(iter_no, mode)

        # 1) WizardDoc Edit aç
        _, res = self._open_wizarddoc_edit_async(wiz_name)
        if res["error"]:
            raise res["error"]

        dlg = self._wait_loadpull_window(title)
        time.sleep(0.2)
        dlg.set_focus()
        time.sleep(0.1)

        # 2) Değerleri gir + kaydet
        self._fill_custom_gamma_points_and_save(params)

        # 3) ESC ile kapat
        self._close_with_esc()

        if run_after_save:
            # 4) WizardDoc'u tekrar aç
            _, res2 = self._open_wizarddoc_edit_async(wiz_name)
            if res2["error"]:
                raise res2["error"]

            dlg2 = self._wait_loadpull_window(title)
            time.sleep(0.2)
            dlg2.set_focus()
            time.sleep(0.1)

            # 5) ENTER ile run
            self._run_with_enter()
            # İstersen tekrar ESC ile çık
            #self._close_with_esc()

        return {"wiz_name": wiz_name, "title": title, "params": params, "run_after_save": run_after_save}

