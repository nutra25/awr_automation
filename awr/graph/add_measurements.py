"""
add_measurement.py
Provides functionality to add new measurements to existing graphs
within the AWR Microwave Office project.
Strictly adheres to the tree-branch logging hierarchy and modular design.
"""

import pyawr.mwoffice as mwoffice
import sys

# Import the logger according to the established architecture
from logger.logger import LOGGER


def add_measurement_to_graph(app, graph_name: str, source_name: str, measurement_expression: str) -> bool:
    """
    Adds a specified measurement to an existing graph in the active AWR project.

    Args:
        app: The active AWR MWOffice COM application instance.
        graph_name (str): The exact name of the target graph.
        source_name (str): The exact name of the source document (e.g., Schematic name).
        measurement_expression (str): The measurement definition (e.g., "DB(|S(2,1)|)").

    Returns:
        bool: True if the measurement was successfully added, False otherwise.
    """
    LOGGER.info(
        f"├── Attempting to add measurement '{measurement_expression}' from '{source_name}' to graph '{graph_name}'")

    try:
        # Verify if the target graph exists by attempting to reference it
        graph = app.Project.Graphs.Item(graph_name)

        # Access the measurements collection and append the new measurement
        measurements = graph.Measurements
        measurements.Add(source_name, measurement_expression)

        LOGGER.info(f"└── Successfully added measurement to graph: '{graph_name}'")
        return True

    except Exception as e:
        LOGGER.error(f"└── Failed to add measurement to graph '{graph_name}'. Exception details: {e}")
        return False


# Standalone Test Execution Block
if __name__ == "__main__":
    LOGGER.info("Starting standalone test sequence for add_measurement.py module.")

    try:
        # Attempt to establish a connection with an active AWR instance
        test_app = mwoffice.CMWOffice()
        LOGGER.info("├── Successfully connected to AWR Microwave Office for testing.")

        # Test Parameters
        # NOTE: For a completely successful test, a graph named "Automated Test Rectangular"
        # and a schematic named "TestSchematic" must already exist in the active AWR project.
        test_target_graph = "Graph 1"
        test_source_doc = "load_data_1"
        test_meas_expr = "G_LPCM(PAE,0.5,12,50,0)[1,*]"

        # Execute the function
        add_measurement_to_graph(test_app, test_target_graph, test_source_doc, test_meas_expr)

        LOGGER.info("└── Test execution sequence completed.")

    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed. Ensure AWR application is running. Details: {ex}")
        sys.exit(1)