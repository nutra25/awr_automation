"""
manager.py (Graph Domain)
Handles all API interactions concerning graphing, data extraction,
marker operations, graph creation, and measurement additions.
"""

import re
from typing import List, Dict, Any

from awr.graph.get_marker_value import get_marker_value
from awr.graph.get_broadband_contours import extract_graph_data
from awr.graph.new_graph import create_new_graph, GraphType
from awr.graph.add_measurements import add_measurement_to_graph
from awr.graph.add_marker import add_marker


class GraphManager:
    """
    Manages AWR Graphic and Data Retrieval operations.
    """
    def __init__(self, app):
        self.app = app

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

    def add_marker(self, graph_name: str, measurement_index: int, x_point: float, data_index: int = 1,
                   trace_index: int = None):
        """Delegates marker attachment to the atomic add_marker module."""
        return add_marker(self.app, graph_name, measurement_index, x_point, data_index, trace_index)