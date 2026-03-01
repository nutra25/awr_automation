"""
manager.py (Graph Domain)
Handles all API interactions concerning graphing, data extraction,
marker operations, graph creation, and measurement additions.
Strictly adheres to the professional coding standards.
"""

import re
from typing import List, Dict, Any, Optional

from awr.graph.get_marker_value import get_marker_value
from awr.graph.get_broadband_contours import extract_graph_data
from awr.graph.new_graph import create_new_graph, GraphType
from awr.graph.add_measurements import add_measurement_to_graph
from awr.graph.add_marker import add_and_move_marker
from awr.graph.move_marker import move_marker
from awr.graph.perform_simulation import perform_simulation
from awr.graph.measurement_toggle import toggle_graph_measurements
from logger.logger import LOGGER


class GraphManager:
    """
    Manages AWR Graphic and Data Retrieval operations.
    """
    def __init__(self, app: Any):
        self.app = app

    def perform_simulation(self) -> bool:
        """Explicitly triggers a simulation analysis."""
        return perform_simulation(self.app)

    def toggle_measurements(self, graph_name: str, enable: bool) -> bool:
        """Enables or disables all measurements on a specified graph."""
        if not self.app.Project.Graphs.Exists(graph_name):
            LOGGER.error(f"│   └── Target graph '{graph_name}' does not exist for toggle operation.")
            return False

        graph = self.app.Project.Graphs(graph_name)
        toggle_graph_measurements(graph, enable)
        return True

    def add_new_graph(self, graph_name: str, graph_type: GraphType) -> bool:
        """Creates a new graph in the project."""
        return create_new_graph(self.app, graph_name, graph_type)

    def add_measurement(self, graph_name: str, source_name: str, measurement_expression: str) -> bool:
        """
        Adds a defined measurement calculation to a specified graph based on a source document.
        """
        return add_measurement_to_graph(self.app, graph_name, source_name, measurement_expression)

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

    def get_broadband_contours(self, graph_name: str) -> Dict[float, List[Dict[str, Any]]]:
        """Extracts broadband contour datasets from the specified graph."""
        return extract_graph_data(self.app, graph_name)

    def add_and_move_marker(self, graph_name: str, measurement_name: str, marker_name: str,
                            action: str = "MIN", search_val: Optional[float] = None,
                            perform_simulation: bool = True) -> None:
        """
        Delegates marker attachment and relocation (MIN/MAX/SEARCH) to the atomic module.
        Includes optional simulation execution prior to marker operations.
        """
        return add_and_move_marker(
            app=self.app,
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
        Delegates the relocation of an existing marker (MIN/MAX/SEARCH) to the atomic module.
        Includes optional simulation execution prior to relocation.
        """
        return move_marker(
            app=self.app,
            graph_name=graph_name,
            marker_name=marker_name,
            action=action,
            search_val=search_val,
            perform_simulation=perform_simulation
        )