"""
create_load_pull_template.py
Provides atomic functionality to execute the AWR Load Pull Template global script.
Implements a bulletproof, focus-independent UI watcher using Windows API (GetWindow).
It directly queries AWR's window tree for active pop-ups and sends a WM_CLOSE
signal, completely bypassing PyAutoGUI and foreground-focus issues.
"""

import pyawr.mwoffice as mwoffice
import sys
import time
import threading
import ctypes
from typing import Any

from logger.logger import LOGGER

# Windows API Constants
GW_ENABLEDPOPUP = 6
WM_CLOSE = 0x0010


def _popup_watcher(main_hwnd: int, timeout: float = 10.0) -> None:
    """
    Background thread worker that queries the AWR main window directly
    to see if it has spawned any blocking modal dialogs (pop-ups).
    If found, it forcefully closes them via direct Windows messaging.
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            # Query the OS specifically for pop-ups owned by AWR
            # This completely ignores whatever window the user is currently looking at (e.g., PyCharm)
            popup_hwnd = ctypes.windll.user32.GetWindow(main_hwnd, GW_ENABLEDPOPUP)

            # If AWR has an active pop-up, popup_hwnd will be different from its main_hwnd
            if popup_hwnd != 0 and popup_hwnd != main_hwnd:
                length = ctypes.windll.user32.GetWindowTextLengthW(popup_hwnd)
                buf = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(popup_hwnd, buf, length + 1)
                window_title = buf.value

                LOGGER.debug(f"│   │   ├── Detected AWR internal dialog: '{window_title}'. Sending close signal...")

                # Send the close signal directly to the dialog's memory address
                ctypes.windll.user32.PostMessageW(popup_hwnd, WM_CLOSE, 0, 0)

                time.sleep(0.5)  # Allow OS to process the close command
                return  # Mission accomplished, thread can exit safely

        except Exception:
            pass

        time.sleep(0.2)  # Prevent CPU spiking


def create_load_pull_template(app: Any, timeout: float = 30.0) -> bool:
    """
    Locates and runs the 'Load Pull Template' routine within AWR Global Scripts.
    Forces script execution to be synchronous and handles internal pop-ups natively.
    """
    LOGGER.info("├── Initiating 'Load Pull Template' generation via Global Scripts...")

    try:
        main_hwnd = app.hWnd
        target_routine = None

        # 1. Locate the specific script routine
        for module in app.GlobalScripts:
            for routine in module.Routines:
                r_name = routine.Name.lower()
                if "load" in r_name and "pull" in r_name and "template" in r_name:
                    target_routine = routine
                    LOGGER.debug(f"│   ├── Found target routine: '{module.Name}.{routine.Name}'")
                    break
            if target_routine:
                break

        if not target_routine:
            LOGGER.error("└── Target routine 'Load Pull Template' not found in Global Scripts.")
            return False

        # 2. Start the bulletproof background pop-up watcher thread
        # daemon=True ensures it won't keep Python open indefinitely if no pop-up appears
        watcher_thread = threading.Thread(target=_popup_watcher, args=(main_hwnd, 10.0), daemon=True)
        watcher_thread.start()

        # 3. Execute the script (This runs asynchronously in AWR API)
        LOGGER.info(f"│   ├── Executing routine '{target_routine.Name}'...")
        target_routine.Run()

        # 4. SYNCHRONIZATION LOCK: Wait for the schematic to physically appear
        LOGGER.debug("│   ├── Waiting for physical generation of the schematic...")
        start_wait = time.time()
        schematic_ready = False

        while (time.time() - start_wait) < timeout:
            try:
                sch = app.Project.Schematics("Load_Pull_Template")
                if sch:
                    schematic_ready = True
                    # CRITICAL: Wait an extra 1.5 seconds here.
                    # The pop-up ALWAYS appears right after the schematic finishes generating.
                    # This wait ensures the Python script doesn't exit before the watcher catches the pop-up.
                    time.sleep(1.5)
                    break
            except Exception:
                pass
            time.sleep(0.5)

        if schematic_ready:
            LOGGER.info("└── Load-Pull schematic template generated successfully.")
            return True
        else:
            LOGGER.error("└── Sequence aborted: Timeout reached before schematic was generated.")
            return False

    except Exception as e:
        LOGGER.error(f"└── Failed to execute Load-Pull template script. Details: {e}")
        return False


# Standalone Test Execution Block
if __name__ == "__main__":
    LOGGER.info("Starting standalone test sequence for create_load_pull_template.py")
    try:
        test_app = mwoffice.CMWOffice()
        create_load_pull_template(test_app)
    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed: {ex}")
        sys.exit(1)