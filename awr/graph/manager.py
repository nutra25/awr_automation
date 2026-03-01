"""
manager.py (Graph Domain)
Handles all API interactions concerning graphing, data extraction,
marker operations, graph creation, and measurement additions.
Strictly adheres to the professional coding standards.
"""
import sys
import re
from typing import List, Dict, Any, Optional

from awr.graph.get_broadband_contours import extract_graph_data
from awr.graph.perform_simulation import perform_simulation

# Import the newly encapsulated domain service classes
from awr.graph.graph import Graph, GraphType
from awr.graph.marker import Marker
from awr.graph.measurement import Measurement
from logger.logger import LOGGER


class GraphManager:
    """
    Manages AWR Graphic and Data Retrieval operations.
    Acts as a facade utilizing specific domain sub-services (Graph, Marker, Measurement).
    """
    def __init__(self, app: Any):
        """
        Initializes the GraphManager and its underlying service objects.

        Args:
            app (Any): The active AWR MWOffice COM application instance.
        """
        self.app = app

        # Instantiate encapsulated domain services
        self.graph_service = Graph(self.app)
        self.marker_service = Marker(self.app)
        self.measurement_service = Measurement(self.app)

    def perform_simulation(self) -> bool:
        """Explicitly triggers a simulation analysis."""
        return perform_simulation(self.app)

    def toggle_measurements(self, graph_name: str, enable: bool) -> bool:
        """Enables or disables all measurements on a specified graph."""
        if not self.app.Project.Graphs.Exists(graph_name):
            LOGGER.error(f"│   └── Target graph '{graph_name}' does not exist for toggle operation.")
            return False

        graph = self.app.Project.Graphs(graph_name)
        self.measurement_service.toggle_graph_measurements(graph, enable)
        return True

    def add_new_graph(self, graph_name: str, graph_type: GraphType) -> bool:
        """Creates a new graph in the project."""
        return self.graph_service.create_new_graph(graph_name, graph_type)

    def add_measurement(self, graph_name: str, source_name: str, measurement_expression: str) -> bool:
        """
        Adds a defined measurement calculation to a specified graph based on a source document.
        """
        return self.measurement_service.add_measurement_to_graph(graph_name, source_name, measurement_expression)

    def get_marker_data(self, graph: str, marker: str, toggle_enable: bool = False) -> List[float]:
        """Retrieves numerical data from a graph marker."""
        raw_output = self.marker_service.get_marker_value(
            graph_title=graph,
            marker_designator=marker,
            perform_simulation=True,
            toggle_enable=toggle_enable
        )

        if not raw_output:
            return [0.0, 0.0, 0.0]

        numbers = re.findall(r"-?\d+\.?\d*", raw_output)
        return [float(n) for n in numbers]

    def get_broadband_contours(self, graph_name: str) -> Dict[float, List[Dict[str, Any]]]:
        """Extracts broadband contour datasets from the specified graph."""
        return extract_graph_data(self.app, graph_name)

    def add_and_move_marker(self, graph_name: str, measurement_name: str, marker_name: str,
                            action: str = "MIN", search_val: Optional[float] = None,
                            perform_simulation: bool = True) -> None:
        """
        Delegates marker attachment and relocation (MIN/MAX/SEARCH) to the Marker service.
        Includes optional simulation execution prior to marker operations.
        """
        return self.marker_service.add_and_move_marker(
            graph_name=graph_name,
            measurement_name=measurement_name,
            marker_name=marker_name,
            action=action,
            search_val=search_val,
            perform_simulation=perform_simulation
        )

    def move_marker(self, graph_name: str, marker_name: str,
                    action: str = "MIN", search_val: Optional[float] = None,
                    perform_simulation: bool = False) -> bool:
        """
        Delegates the relocation of an existing marker (MIN/MAX/SEARCH) to the Marker service.
        Includes optional simulation execution prior to relocation.
        """
        return self.marker_service.move_marker(
            graph_name=graph_name,
            marker_name=marker_name,
            action=action,
            search_val=search_val,
            perform_simulation=perform_simulation
        )


if __name__ == "__main__":
    import pyawr.mwoffice as mwoffice

    LOGGER.info("├── Starting standalone test sequence for manager.py")
    try:
        test_app = mwoffice.CMWOffice()
        graph_manager = GraphManager(app=test_app)

        target_graph = "Results"

        LOGGER.info(f"│   ├── Initializing Manager with encapsulated domain classes...")

        if test_app.Project.Graphs.Exists(target_graph):
            graph_manager.toggle_measurements(target_graph, False)
            LOGGER.info("│   ├── Successfully toggled measurements using encapsulated class logic.")

        LOGGER.info("└── Test execution sequence completed successfully.")
    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed: {ex}")
        sys.exit(1)