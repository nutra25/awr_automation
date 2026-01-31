# awr_pullsim_finish_waiter.py
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any

import win32com.client


@dataclass(frozen=True)
class WaitResult:
    ok: bool
    info: Dict[str, Any]

import pyawr

class AwrSimFinishWaiter:
    """
    AWR Status Window üzerinden "End Simulate" + match_text ile sim bitti algılayıcı.

    Kullanım:
        w = AwrSimFinishWaiter(progid="AWR.MWOffice.19.0")
        ok, info = w.wait(timeout_s=1800, match_text="LP_it2_LP_Sim")
    """
    def __init__(self, progid: str = "AWR.MWOffice.19.0"):
        self.progid = progid
        self._app = None  # cached COM app

    # ---------- Public API ----------

    def get_app(self):
        """AWR COM bağlantısını al (cache'li)."""
        if self._app is not None:
            return self._app
        try:
            self._app = win32com.client.GetActiveObject(self.progid)
        except Exception:
            self._app = win32com.client.Dispatch(self.progid)
        return self._app

    def wait(
        self,
        timeout_s: float = 3600,
        poll_s: float = 0.5,
        match_text: Optional[str] = None,
        clear: bool = True,
        category: int = -1,
    ) -> WaitResult:
        """
        match_text:
          None  -> sadece "End Simulate" arar
          str   -> "End Simulate" ve match_text birlikte gate'ler

        clear:
          True  -> mümkünse status'u temizler (en deterministik)
          False -> baseline ile yeni log gelmesini yakalar
        """
        app = self.get_app()
        src_name, st = self._get_status_obj(app)

        search_target = st
        if not hasattr(search_target, "Search") and hasattr(st, "Window"):
            search_target = st.Window

        cleared = False
        if clear:
            cleared = self._clear_status(search_target)

        base_end = self._count_items(self._search_status(search_target, "End Simulate", category))
        base_match = 0
        if match_text:
            base_match = self._count_items(self._search_status(search_target, match_text, category))

        t0 = time.time()
        while time.time() - t0 < timeout_s:
            end_n = self._count_items(self._search_status(search_target, "End Simulate", category))

            if match_text:
                match_n = self._count_items(self._search_status(search_target, match_text, category))
                if (end_n > base_end) and (match_n >= base_match):
                    return WaitResult(True, {
                        "source": src_name,
                        "cleared": cleared,
                        "end_simulate_count": end_n,
                        "baseline_end": base_end,
                        "match_text": match_text,
                        "match_count": match_n,
                        "baseline_match": base_match,
                    })
            else:
                if end_n > base_end:
                    return WaitResult(True, {
                        "source": src_name,
                        "cleared": cleared,
                        "end_simulate_count": end_n,
                        "baseline_end": base_end,
                    })

            time.sleep(poll_s)

        return WaitResult(False, {
            "source": src_name,
            "cleared": cleared,
            "timeout_s": timeout_s,
            "baseline_end": base_end,
            "match_text": match_text,
        })

    # ---------- Internals ----------

    def _get_status_obj(self, app) -> Tuple[str, Any]:
        candidates = [
            ("Status", lambda a: a.Status),
            ("StatusWindow", lambda a: a.StatusWindow),
            ("Status.Window", lambda a: a.Status.Window),
        ]
        last_err = None
        for name, fn in candidates:
            try:
                obj = fn(app)
                _ = obj
                return name, obj
            except Exception as e:
                last_err = e
        raise RuntimeError(f"Status objesi bulunamadı. Son hata: {last_err}")

    def _count_items(self, items) -> int:
        try:
            return int(items.Count)
        except Exception:
            n = 0
            try:
                for _ in items:
                    n += 1
            except Exception:
                pass
            return n

    def _clear_status(self, status_obj) -> bool:
        if hasattr(status_obj, "RemoveAllItems"):
            status_obj.RemoveAllItems()
            return True
        return False

    def _search_status(self, status_obj, text: str, category: int = -1):
        if hasattr(status_obj, "Search"):
            return status_obj.Search(text, category)
        if hasattr(status_obj, "Items") and hasattr(status_obj.Items, "Search"):
            return status_obj.Items.Search(text, category)
        raise RuntimeError("Search metodu bulunamadı.")


# --------- Basit fonksiyon arayüzü (en kolay import) ---------

_default_waiter = AwrSimFinishWaiter()


def wait_sim_finished(
    match_text: str,
    timeout_s: float = 1800,
    poll_s: float = 0.5,
    clear: bool = True,
    progid: str = "AWR.MWOffice.19.0",
) -> Tuple[bool, Dict[str, Any]]:
    """
    Tek satır kullanım için helper.

    Ör:
        ok, info = wait_sim_finished("LP_it2_LP_Sim")
    """
    if progid != _default_waiter.progid:
        # farklı progid istenirse yeni instance aç
        waiter = AwrSimFinishWaiter(progid=progid)
        r = waiter.wait(timeout_s=timeout_s, poll_s=poll_s, match_text=match_text, clear=clear)
    else:
        r = _default_waiter.wait(timeout_s=timeout_s, poll_s=poll_s, match_text=match_text, clear=clear)

    return r.ok, r.info
