"""
toggle_measurements.py
Provides atomic functionality to enable or disable all measurements on a specific AWR graph.
Strictly adheres to the tree-branch logging hierarchy and error handling protocols.
"""

import sys
from typing import Any
from logger.logger import LOGGER


def toggle_graph_measurements(graph: Any, enable: bool) -> None:
    """
    Enables or disables all measurements associated with the provided graph object.

    Args:
        graph (Any): The AWR graph COM object.
        enable (bool): True to enable measurements, False to disable them.

    Raises:
        RuntimeError: If the toggle operation fails.
    """
    state_str = "Enabling" if enable else "Disabling"
    LOGGER.debug(f"│   ├── {state_str} measurements for graph '{graph.Name}'...")

    try:
        for meas in graph.Measurements:
            meas.Enabled = enable
    except Exception as e:
        LOGGER.error(f"│   └── Failed to toggle measurements for graph '{graph.Name}': {e}")
        raise RuntimeError(f"Measurement toggle operation failed: {e}")


if __name__ == "__main__":
    import pyawr.mwoffice as mwoffice

    LOGGER.info("├── Starting standalone test sequence for toggle_measurements.py")
    try:
        test_app = mwoffice.CMWOffice()
        target_graph_name = "Results"

        if test_app.Project.Graphs.Exists(target_graph_name):
            test_graph = test_app.Project.Graphs(target_graph_name)

            # Test Case 1: Enable measurements
            toggle_graph_measurements(test_graph, enable=True)

            # Test Case 2: Disable measurements
            toggle_graph_measurements(test_graph, enable=False)

            LOGGER.info("└── Test execution sequence completed successfully.")
        else:
            LOGGER.warning(f"└── Test skipped: Graph '{target_graph_name}' does not exist.")
    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed: {ex}")
        sys.exit(1)