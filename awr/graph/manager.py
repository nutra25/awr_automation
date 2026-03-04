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
from awr.graph.get_measurement_data import extract_single_point_data

# Import the newly encapsulated domain service classes
from awr.graph.graph import Graph, GraphType, MarkerDisplayFormat
from awr.graph.marker import Marker
from awr.graph.measurement import Measurement
from core.logger import logger


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
            logger.error(f"│   └── Target graph '{graph_name}' does not exist for toggle operation.")
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

    def set_graph_marker_display_format(self, graph_name: str, display_format: MarkerDisplayFormat) -> bool:
        """
        Sets the global display format for all markers on a specified graph.
        Requires a MarkerFormat enum for strict type safety.
        """
        return self.graph_service.set_graph_marker_display_format(graph_name, display_format)

    def get_single_measurement_data(self, graph_name: str, measurement_name: str) -> List[Any]:
        """
        Delegates the extraction of generic, raw measurement data to the specialized module.
        Preserves original data dimensionality.
        """
        raw_data = extract_single_point_data(self.app, graph_name, measurement_name)

        if not raw_data:
            logger.warning("└── No valid data extracted from AWR environment. Returning an empty list.")
            return []

        return raw_data

if __name__ == "__main__":
    import pyawr.mwoffice as mwoffice

    logger.info("├── Starting standalone test sequence for manager.py")
    try:
        test_app = mwoffice.CMWOffice()
        graph_manager = GraphManager(app=test_app)

        target_graph = "Results"

        logger.info(f"│   ├── Initializing Manager with encapsulated domain classes...")

        if test_app.Project.Graphs.Exists(target_graph):
            graph_manager.toggle_measurements(target_graph, False)
            logger.info("│   ├── Successfully toggled measurements using encapsulated class logic.")

        logger.info("└── Test execution sequence completed successfully.")
    except Exception as ex:
        logger.critical(f"└── Test execution failed: {ex}")
        sys.exit(1)