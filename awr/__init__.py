import time
import subprocess
import os
import pyawr.mwoffice as mwoffice

from core.logger import logger

from .graph import Graph
from .project import Project
from .wizard import Wizard
from .data_file import DataFile
from .schematic import Schematic

class Awr:
    def __init__(self, exe_path: str = None):
        self.logger = logger
        self.app = self._initialize_application(exe_path)

        self.graph = Graph(self)
        self.schematic = Schematic(self)
        self.data_file = DataFile(self)
        self.project = Project(self)
        self.wizard = Wizard(self)

    def _initialize_application(self, exe_path: str, timeout: int = 60):
        """
        Robust connection logic featuring auto-launch capabilities and a controlled timeout loop.
        """
        self.logger.info("├── Initializing AWR Microwave Office Application...")
        # noinspection PyBroadException
        try:
            app = mwoffice.CMWOffice()
            self.logger.info("└── Successfully connected to active session.")
            return app
        except Exception:
            self.logger.debug("├── No active session found.")


        if exe_path:
            if os.path.exists(exe_path):
                self.logger.info(f"├── Launching new instance from: {exe_path}")
                try:
                    subprocess.Popen(exe_path)
                except Exception as e:
                    self.logger.critical(f"└── Failed to launch executable: {e}")
                    raise
            else:
                self.logger.warning(f"├── Executable path not found: {exe_path}")
                self.logger.warning("├── Waiting for manual start...")
        else:
            self.logger.warning("├── No executable path provided. Waiting for manual start...")

        self.logger.info(f"├── Waiting for application to initialize (Timeout: {timeout}s)...")
        start_time = time.time()

        while (time.time() - start_time) < timeout:
            # noinspection PyBroadException
            try:
                app = mwoffice.CMWOffice()
                self.logger.info("└── Application started and connected successfully.")
                return app
            except Exception:
                time.sleep(2)

        logger.critical("└── Timeout reached: Application failed to start or connect.")
        raise TimeoutError("MWOffice failed to start within the allocated time.")

