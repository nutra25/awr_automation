"""
add_marker.py
Provides atomic functionality to attach a marker to a specific measurement
trace within an AWR graph.
Strictly adheres to the tree-branch logging hierarchy and error handling protocols.
"""

import sys
from typing import Any, Optional
from logger.logger import LOGGER


def add_marker(
        app: Any,
        graph_name: str,
        measurement_index: int,
        x_point: float,
        data_index: int = 1,
        trace_index: Optional[int] = None
) -> Optional[Any]:
    """
    Attaches a marker to a specified graph measurement at a given X-axis point.

    Args:
        app (Any): The active AWR MWOffice COM application instance.
        graph_name (str): The target graph name.
        measurement_index (int): The index of the measurement (1-based).
        x_point (float): The X-axis (sweep) value where the marker will be placed.
        data_index (int, optional): The data index. Defaults to 1.
        trace_index (int, optional): The specific trace index for multi-trace measurements.
                                     Defaults to None.

    Returns:
        The instantiated marker COM object, or None if the operation fails.
    """
    LOGGER.info(f"├── Initiating marker attachment sequence for graph: '{graph_name}'")

    try:
        project = app.Project

        # Pre-validation: Ensure the target graph exists
        if not project.Graphs.Exists(graph_name):
            LOGGER.error(f"└── Sequence aborted: Target graph '{graph_name}' does not exist.")
            return None

        graph = project.Graphs(graph_name)
        markers = graph.Markers

        # Branching logic based on the presence of a specific trace index
        if trace_index is not None:
            LOGGER.debug(f"│   ├── Utilizing AddEx method (Target Trace Index: {trace_index})")
            new_marker = markers.AddEx(measurement_index, data_index, x_point, trace_index)
        else:
            LOGGER.debug(f"│   ├── Utilizing standard Add method (Measurement Index: {measurement_index})")
            new_marker = markers.Add(measurement_index, data_index, x_point)

        LOGGER.info(f"└── Successfully attached marker at X={x_point} (Measurement: {measurement_index}).")
        return new_marker

    except Exception as e:
        LOGGER.error(f"└── Failed to attach marker to graph '{graph_name}'. Exception details: {e}")
        return None


if __name__ == "__main__":
    import pyawr.mwoffice as mwoffice

    LOGGER.info("├── Starting standalone test sequence for add_marker.py")
    try:
        test_app = mwoffice.CMWOffice()

        # Ensure the specified graph exists in the open project before execution
        test_graph = "Results"

        # Test Case 1: Standard marker addition
        add_marker(test_app, test_graph, measurement_index=1, x_point=12.5)

        # Test Case 2: Specific trace marker addition (Uncomment to test)
        # add_marker(test_app, test_graph, measurement_index=1, x_point=13.0, trace_index=1)

        LOGGER.info("└── Test execution sequence completed successfully.")
    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed: {ex}")
        sys.exit(1)