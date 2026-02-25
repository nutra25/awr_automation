"""
awr_driver.py
Central Hub for AWR Microwave Office API operations.
Employs composition to delegate specific tasks to dedicated domain managers.
"""

import time
import subprocess
import os
import pyawr.mwoffice as mwoffice

from logger.logger import LOGGER

# Domain Managers Integration
from awr.project.manager import ProjectManager
from awr.circuit_schematic.manager import CircuitSchematicManager
from awr.graph.manager import GraphManager
from awr.wizard.manager import WizardManager


class AWRDriver:
    """
    Independent wrapper for AWR API.
    Initializes the COM object and routes domain-specific commands to sub-managers.
    """

    def __init__(self, exe_path: str = None):
        """
        Initializes the application connection and instantiates domain managers.
        """
        self.app = self._initialize_application(exe_path)

        # Initialize Sub-Domain Managers with the active COM object
        LOGGER.info("├── Instantiating domain-specific manager modules...")
        self.project = ProjectManager(self.app)
        self.circuit = CircuitSchematicManager(self.app)
        self.graph = GraphManager(self.app)
        self.wizard = WizardManager(self.app)
        LOGGER.info("└── Domain managers successfully initialized.")

    def _initialize_application(self, exe_path: str, timeout: int = 60):
        """
        Robust connection logic featuring auto-launch capabilities and a controlled timeout loop.
        """
        LOGGER.info("├── Initializing AWR Microwave Office Application...")

        try:
            app = mwoffice.CMWOffice()
            LOGGER.info("└── Successfully connected to active session.")
            return app
        except Exception:
            LOGGER.debug("├── No active session found.")

        if exe_path:
            if os.path.exists(exe_path):
                LOGGER.info(f"├── Launching new instance from: {exe_path}")
                try:
                    subprocess.Popen(exe_path)
                except Exception as e:
                    LOGGER.critical(f"└── Failed to launch executable: {e}")
                    raise
            else:
                LOGGER.warning(f"├── Executable path not found: {exe_path}")
                LOGGER.warning("├── Waiting for manual start...")
        else:
            LOGGER.warning("├── No executable path provided. Waiting for manual start...")

        LOGGER.info(f"├── Waiting for application to initialize (Timeout: {timeout}s)...")
        start_time = time.time()

        while (time.time() - start_time) < timeout:
            try:
                app = mwoffice.CMWOffice()
                LOGGER.info("└── Application started and connected successfully.")
                return app
            except Exception:
                time.sleep(2)

        LOGGER.critical("└── Timeout reached: Application failed to start or connect.")
        raise TimeoutError("MWOffice failed to start within the allocated time.")