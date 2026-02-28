"""
new_graph.py
Provides functionality to create new graphs within the AWR Microwave Office project.
Utilizes enumerations to ensure type safety and enable IDE autocomplete features.
Includes input validation to enforce AWR naming conventions.
"""

import pyawr.mwoffice as mwoffice
from enum import Enum
import sys
import re

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


def create_new_graph(app, graph_name: str, graph_type: GraphType = GraphType.RECTANGULAR) -> bool:
    """
    Creates a new graph in the active AWR project.

    Args:
        app: The active AWR MWOffice COM application instance.
        graph_name (str): The exact name to be assigned to the new graph.
        graph_type (GraphType): The desired graph type, selected from the GraphType enum.

    Returns:
        bool: True if the graph was created successfully, False otherwise.
    """
    LOGGER.info(f"├── Attempting to create new graph: '{graph_name}' (Type: {graph_type.name})")

    # Validation: AWR only allows A-Z, a-z, 0-9, underscores (_), and spaces.
    if not re.match(r'^[A-Za-z0-9_ ]+$', graph_name):
        LOGGER.error("└── Invalid graph name. Only alphanumeric characters, underscores, and spaces are permitted.")
        return False

    try:
        graphs = app.Project.Graphs

        # Verify if a graph with the same name already exists to prevent duplication errors
        for i in range(1, graphs.Count + 1):
            if graphs.Item(i).Name == graph_name:
                LOGGER.warning(f"└── Graph '{graph_name}' already exists. Creation aborted.")
                return False

        # Create the graph using the integer value from the enum
        graphs.Add(graph_name, graph_type.value)
        LOGGER.info(f"└── Successfully created graph: '{graph_name}'")
        return True

    except Exception as e:
        LOGGER.error(f"└── Failed to create graph '{graph_name}'. Exception: {e}")
        return False


# Standalone Test Execution Block
if __name__ == "__main__":
    LOGGER.info("Starting standalone test sequence for new_graph.py module.")

    try:
        # Attempt to establish a connection with an active AWR instance
        test_app = mwoffice.CMWOffice()
        LOGGER.info("├── Successfully connected to AWR Microwave Office for testing.")

        # Test Case 1: Create a standard rectangular graph (Hyphens removed to comply with AWR rules)
        test_name_1 = "Automated Test Rectangular"
        create_new_graph(test_app, test_name_1, GraphType.RECTANGULAR)

        # Test Case 2: Create a Smith Chart
        test_name_2 = "Automated Test Smith Chart"
        create_new_graph(test_app, test_name_2, GraphType.SMITH_CHART)

        # Test Case 3: Attempt to create a duplicate graph to verify error handling
        LOGGER.info("├── Verifying duplicate graph handling logic...")
        create_new_graph(test_app, test_name_1, GraphType.RECTANGULAR)

        # Test Case 4: Verify invalid character prevention
        LOGGER.info("├── Verifying invalid character sanitization logic...")
        create_new_graph(test_app, "Invalid-Name-Test!", GraphType.RECTANGULAR)

        LOGGER.info("└── Test execution sequence completed successfully.")

    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed. Ensure AWR application is running. Details: {ex}")
        sys.exit(1)