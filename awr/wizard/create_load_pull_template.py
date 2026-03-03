"""
create_load_pull_template.py
Provides atomic functionality to execute the AWR Load Pull Template global script.
"""

import pyawr.mwoffice as mwoffice
import sys
import time
from typing import Any

from core.logger import LOGGER

def create_load_pull_template(app: Any, timeout: float = 30.0) -> bool:
    """
    Locates and runs the 'Load Pull Template' routine within AWR Global Scripts.
    Forces script execution to be synchronous by waiting for the schematic to generate.
    """
    LOGGER.info("├── Initiating 'Load Pull Template' generation via Global Scripts...")

    try:
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

        # 2. Execute the script (This runs asynchronously in AWR API)
        LOGGER.info(f"│   ├── Executing routine '{target_routine.Name}'...")
        target_routine.Run()

        # 3. SYNCHRONIZATION LOCK: Wait for the schematic to physically appear
        LOGGER.debug("│   ├── Waiting for physical generation of the schematic...")
        start_wait = time.time()
        schematic_ready = False

        while (time.time() - start_wait) < timeout:
            try:
                # Try to access the schematic to see if it has been created
                sch = app.Project.Schematics("Load_Pull_Template")
                if sch:
                    schematic_ready = True
                    break
            except Exception:
                # Expected to fail until the schematic is actually created
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