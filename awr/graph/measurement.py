"""
measurement.py
"""
import sys
from typing import Any
import pyawr.mwoffice as mwoffice
from logger.logger import LOGGER


class Measurement:
    """
    Service class managing graph measurement operations.
    """
    def __init__(self, app: Any):
        """
        Initializes the Measurement operations class.

        Args:
            app (Any): The active AWR MWOffice COM application instance.
        """
        self.app = app

    def toggle_graph_measurements(self, graph: Any, enable: bool) -> None:
        """
        Enables or disables all measurements associated with the provided graph object.

        Args:
            graph (Any): The AWR graph COM object.
            enable (bool): True to enable measurements, False to disable them.
        """
        state_str = "Enabling" if enable else "Disabling"
        LOGGER.debug(f"│   ├── {state_str} measurements for graph '{graph.Name}'...")

        try:
            for meas in graph.Measurements:
                meas.Enabled = enable
        except Exception as e:
            LOGGER.error(f"│   └── Failed to toggle measurements for graph '{graph.Name}': {e}")
            raise RuntimeError(f"Measurement toggle operation failed: {e}")

    def add_measurement_to_graph(self, graph_name: str, source_name: str, measurement_expression: str) -> bool:
        """
        Adds a specified measurement to an existing graph in the active AWR project.

        Args:
            graph_name (str): The exact name of the target graph.
            source_name (str): The exact name of the source document (e.g., Schematic name).
            measurement_expression (str): The measurement definition (e.g., "DB(|S(2,1)|)").

        Returns:
            bool: True if the measurement was successfully added, False otherwise.
        """
        LOGGER.info(f"├── Attempting to add measurement '{measurement_expression}' from '{source_name}' to graph '{graph_name}'")

        try:
            graph = self.app.Project.Graphs.Item(graph_name)
            measurements = graph.Measurements
            measurements.Add(source_name, measurement_expression)

            LOGGER.info(f"└── Successfully added measurement to graph: '{graph_name}'")
            return True

        except Exception as e:
            LOGGER.error(f"└── Failed to add measurement to graph '{graph_name}'. Exception details: {e}")
            return False

    def find_measurement(self):
        """
        Placeholder for future functionality to locate specific measurements.
        """
        LOGGER.debug("│   ├── find_measurement method is reserved for future implementation.")
        pass


if __name__ == "__main__":
    LOGGER.info("├── Starting standalone test sequence for measurement.py")
    try:
        test_app = mwoffice.CMWOffice()
        measurement_service = Measurement(test_app)

        target_graph_name = "Results"

        if test_app.Project.Graphs.Exists(target_graph_name):
            test_graph = test_app.Project.Graphs(target_graph_name)

            LOGGER.info(f"│   ├── Testing toggle operations on graph: '{target_graph_name}'")
            measurement_service.toggle_graph_measurements(test_graph, enable=True)
            measurement_service.toggle_graph_measurements(test_graph, enable=False)

            LOGGER.info("└── Test execution sequence completed successfully.")
        else:
            LOGGER.warning(f"└── Test skipped: Graph '{target_graph_name}' does not exist.")
    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed: {ex}")
        sys.exit(1)