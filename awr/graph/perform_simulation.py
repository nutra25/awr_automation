"""
perform_simulation.py
Provides functionality to execute the AWR simulator analysis.
Strictly adheres to the tree-branch logging hierarchy and error handling protocols.
"""

from typing import Any
from core.logger import LOGGER

def perform_simulation(app: Any) -> bool:
    """
    Triggers the simulation analysis in the active AWR project.

    Args:
        app (Any): The active AWR MWOffice COM application instance.

    Returns:
        bool: True if the simulation completes successfully, False otherwise.

    Raises:
        RuntimeError: If the simulation execution fails.
    """
    try:
        project = app.Project
        # Simulation steps are logged as DEBUG to keep the console output clean
        LOGGER.debug("│   ├── Starting Simulation (Analyze)...")
        simulator = project.Simulator
        simulator.Analyze()
        LOGGER.debug("│   ├── Simulation Completed.")
        return True
    except Exception as sim_error:
        LOGGER.critical(f"│   └── Simulation FAILED: {sim_error}")
        raise RuntimeError(f"Simulation execution failed: {sim_error}")