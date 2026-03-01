"""
graph.py
Encapsulates all operations related to AWR Microwave Office graphs.
Currently handles the creation of new graphs, designed to be extensible
for future graphing capabilities.
Strictly adheres to the tree-branch logging hierarchy.
"""

import sys
import re
from enum import Enum
from typing import Any
import pyawr.mwoffice as mwoffice
from logger.logger import LOGGER


class GraphType(Enum):
    """
    Enumeration of available graph types in AWR Microwave Office.
    Provides strict type hinting and IDE intellisense support.
    """
    RECTANGULAR = mwoffice.mwGraphType.mwGT_Rectangular
    SMITH_CHART = mwoffice.mwGraphType.mwGT_SmithChart
    POLAR = mwoffice.mwGraphType.mwGT_Polar
    RECTANGULAR_COMPLEX = mwoffice.mwGraphType.mwGT_RectangularComplex
    TABULAR = mwoffice.mwGraphType.mwGT_Tabular
    ANTENNA = mwoffice.mwGraphType.mwGT_Antenna
    HISTOGRAM = mwoffice.mwGraphType.mwGT_Histogram
    THREE_DIMENSIONAL = mwoffice.mwGraphType.mwGT_ThreeDim
    CONSTELLATION = mwoffice.mwGraphType.mwGT_Constellation


class Graph:
    """
    Service class managing the lifecycle and operations of AWR graphs.
    """

    def __init__(self, app: Any):
        """
        Initializes the Graph operations class.

        Args:
            app (Any): The active AWR MWOffice COM application instance.
        """
        self.app = app

    def create_new_graph(self, graph_name: str, graph_type: GraphType = GraphType.RECTANGULAR) -> bool:
        """
        Creates a new graph in the active AWR project.

        Args:
            graph_name (str): The exact name to be assigned to the new graph.
            graph_type (GraphType): The desired graph type, selected from the GraphType enum.

        Returns:
            bool: True if the graph was created successfully, False otherwise.
        """
        LOGGER.info(f"├── Attempting to create new graph: '{graph_name}' (Type: {graph_type.name})")

        if not re.match(r'^[A-Za-z0-9_ ]+$', graph_name):
            LOGGER.error("└── Invalid graph name. Only alphanumeric characters, underscores, and spaces are permitted.")
            return False

        try:
            graphs = self.app.Project.Graphs

            for i in range(1, graphs.Count + 1):
                if graphs.Item(i).Name == graph_name:
                    LOGGER.warning(f"└── Graph '{graph_name}' already exists. Creation aborted.")
                    return False

            graphs.Add(graph_name, graph_type.value)
            LOGGER.info(f"└── Successfully created graph: '{graph_name}'")
            return True

        except Exception as e:
            LOGGER.error(f"└── Failed to create graph '{graph_name}'. Exception: {e}")
            return False


if __name__ == "__main__":
    LOGGER.info("├── Starting standalone test sequence for graph.py")
    try:
        test_app = mwoffice.CMWOffice()
        graph_service = Graph(test_app)

        test_graph_name = "Automated Test Rectangular"
        graph_service.create_new_graph(test_graph_name, GraphType.RECTANGULAR)

        LOGGER.info("└── Test execution sequence completed successfully.")
    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed: {ex}")
        sys.exit(1)