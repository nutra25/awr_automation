import time
import subprocess
import os
import pyawr.mwoffice as mwoffice
from logger import LOGGER


def open_awr(exe_path: str = None, timeout: int = 60):
    """
    Attempts to connect to the AWR Microwave Office application.
    If the application is not running, it attempts to launch it provided a valid path
    is given, or waits for the user to start it manually within the timeout period.

    Args:
        exe_path (str): Full path to the MWOffice.exe executable (Optional).
        timeout (int): Maximum time in seconds to wait for a connection (Default: 60s).

    Returns:
        The active AWR application object.

    Raises:
        TimeoutError: If the application cannot be connected to within the specified time.
    """

    LOGGER.info("Attempting to connect to AWR Microwave Office application...")

    # Attempt to connect to an existing session first
    try:
        app = mwoffice.CMWOffice()
        LOGGER.info(" └── Successfully connected to the active AWR session.")
        return app
    except Exception:
        # Handle the case where the application is not currently open
        LOGGER.debug(" ├─ No active session found. Preparing to launch or wait...")

        if exe_path and os.path.exists(exe_path):
            LOGGER.info(f" ├── Launching AWR from: {exe_path}")
            subprocess.Popen(exe_path)
        elif exe_path:
            LOGGER.warning(f" ├─ WARNING: Specified executable path not found: {exe_path}")
            LOGGER.info(" ├── Waiting for manual start or path correction...")
        else:
            LOGGER.info(" ├── Application not open. Waiting for manual start...")

    # Begin the waiting loop until the timeout is reached
    start_time = time.time()

    while (time.time() - start_time) < timeout:
        try:
            # Retry connection
            app = mwoffice.CMWOffice()
            LOGGER.info(" └── Application started and connected successfully!")
            return app
        except Exception:
            # Wait briefly before the next attempt
            time.sleep(2)
            # Keeping the console clean without spamming logs during the wait
            pass

    # Log critical failure if timeout occurs
    LOGGER.critical(" └── Timeout reached: MWOffice could not be opened or connected.")
    raise TimeoutError("MWOffice could not be opened or connected within the specified timeout.")