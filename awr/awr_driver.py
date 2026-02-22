import time
import subprocess
import os
import pyawr.mwoffice as mwoffice
from typing import List, Dict, Any, Union
import re

# Import modular functions
from awr.graph.awr_get_marker_value import get_marker_value
from awr.circuit_schematic.awr_configure_schematic_element import configure_schematic_element
from awr.wizard.awr_loadpull_wizard import run_loadpull_wizard
from awr.circuit_schematic.awr_configure_schematic_rf_frequency import configure_schematic_rf_frequency
from awr.graph.awr_get_broadband_contours import extract_graph_data
from awr.project.awr_project_saveas import save_project_as
from awr.project.open_project import open_project

from config import SCHEMATIC_NAME
from logger.logger import LOGGER


class AWRDriver:
    """
    Static interface wrapper for AWR Microwave Office API operations.
    Handles application connection, project management, and simulation tasks.
    """

    def __init__(self, exe_path: str = None):
        """
        Initializes the AWR driver by connecting to an active session or launching a new one.

        Args:
            exe_path: Full path to MWOffice.exe to launch if not currently running.
        """
        self.app = self._initialize_application(exe_path)

    def _initialize_application(self, exe_path: str, timeout: int = 60):
        """
        Robust connection logic featuring auto-launch capabilities and a controlled timeout loop.
        """
        LOGGER.info("├── Initializing AWR Microwave Office Application...")

        # Attempt to establish a connection with a currently active session
        try:
            app = mwoffice.CMWOffice()
            LOGGER.info("└── Successfully connected to active session.")
            return app
        except Exception:
            LOGGER.debug("├── No active session found.")

        # Launch a new instance if a valid executable path is provided
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

        # Monitor the application initialization process within the timeout boundary
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

    def save_current_project_as(self, save_path: str) -> None:
        """Wrapper method delegating the save operation to the dedicated module."""
        save_project_as(self.app, save_path)

    def open_existing_project(self, project_path: str) -> bool:
        """Wrapper method delegating the load operation to the dedicated module."""
        return open_project(self.app, project_path)

    def configure_element(self, element_name: str, params: Dict[str, Any]) -> None:
        """Configures a schematic element with the provided parameters."""
        configure_schematic_element(
            self.app,
            schematic_title=SCHEMATIC_NAME,
            target_designator=element_name,
            parameter_map=params,
        )

    def set_frequency(self, freq: Union[float, List[float]]) -> None:
        """Updates the system simulation frequency."""
        configure_schematic_rf_frequency(
            self.app,
            schematic_name=SCHEMATIC_NAME,
            frequencies=freq
        )

    def get_marker_data(self, graph: str, marker: str, toggle_enable: bool = False) -> List[float]:
        """Retrieves numerical data from a graph marker."""
        raw_output = get_marker_value(
            self.app,
            graph_title=graph,
            marker_designator=marker,
            perform_simulation=True,
            toggle_enable=toggle_enable
        )

        if not raw_output:
            return [0.0, 0.0, 0.0]

        numbers = re.findall(r"-?\d+\.?\d*", raw_output)
        return [float(n) for n in numbers]

    def run_wizard(self, options: Dict[str, Any]) -> None:
        """Triggers the Load Pull Wizard with the specified configuration."""
        run_loadpull_wizard(self.app, options)

    def get_broadband_contours(self, graph_name: str) -> Dict[float, List[Dict[str, Any]]]:
        """Extracts broadband contour data from the specified graph."""
        return extract_graph_data(self.app, graph_name)