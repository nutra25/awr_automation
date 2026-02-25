"""
manager.py (Graph Domain)
Handles all API interactions concerning graphing, data extraction,
and marker operations.
"""

import re
from typing import List, Dict, Any
from awr.graph.awr_get_marker_value import get_marker_value
from awr.graph.awr_get_broadband_contours import extract_graph_data

class GraphManager:
    """
    Manages AWR Graphic and Data Retrieval operations.
    """
    def __init__(self, app):
        self.app = app

    def get_marker_data(self, graph: str, marker: str, toggle_enable: bool = False) -> List[float]:
        """
        Retrieves numerical data from a graph marker and processes it into
        a structured floating point list.
        """
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