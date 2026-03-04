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
from core.logger import logger


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

class MarkerDisplayFormat(Enum):
    """
    Enumeration of available marker display formats in AWR Microwave Office.
    Provides strict type hinting and prevents hard-coded values.
    """
    MAGNITUDE_ANGLE = mwoffice.mwGraphMarkerFormat.mwGMF_MagnitudeAngle
    REAL_IMAGINARY = mwoffice.mwGraphMarkerFormat.mwGMF_RealImaginary
    DB_MAGNITUDE_ANGLE = mwoffice.mwGraphMarkerFormat.mwGMF_MagnitudeAngle

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
        logger.info(f"├── Attempting to create new graph: '{graph_name}' (Type: {graph_type.name})")

        if not re.match(r'^[A-Za-z0-9_ ]+$', graph_name):
            logger.error("└── Invalid graph name. Only alphanumeric characters, underscores, and spaces are permitted.")
            return False

        try:
            graphs = self.app.Project.Graphs

            for i in range(1, graphs.Count + 1):
                if graphs.Item(i).Name == graph_name:
                    logger.warning(f"└── Graph '{graph_name}' already exists. Creation aborted.")
                    return False

            graphs.Add(graph_name, graph_type.value)
            logger.info(f"└── Successfully created graph: '{graph_name}'")
            return True

        except Exception as e:
            logger.error(f"└── Failed to create graph '{graph_name}'. Exception: {e}")
            return False

    def set_graph_marker_display_format(self, graph_name: str, display_format: MarkerDisplayFormat) -> bool:
        """
        Updates the marker display format for a specified graph.

        Args:
            graph_name (str): The exact name of the target graph.
            display_format (MarkerDisplayFormat): The desired display format from the MarkerFormat enum.

        Returns:
            bool: True if the format was updated successfully, False otherwise.
        """
        logger.info(f"├── Attempting to set marker format for graph '{graph_name}' to '{display_format.name}'")

        try:
            if not self.app.Project.Graphs.Exists(graph_name):
                logger.error(f"└── Target graph '{graph_name}' does not exist.")
                return False

            graph = self.app.Project.Graphs(graph_name)
            graph.Markers.Options.DisplayFormat = display_format.value

            logger.info(f"└── Successfully updated marker format for '{graph_name}'.")
            return True

        except Exception as e:
            logger.error(f"└── Failed to update marker format for '{graph_name}'. Exception: {e}")
            return False

    def get_single_measurement_data(self, measurement_name: str) -> list:
        """
        Locates the specified measurement within this graph instance and retrieves
        all Y-dimension values associated with the first X-data point.

        Args:
            measurement_name (str): Name of the target measurement to find.

        Returns:
            list: A list of Y-axis values (e.g., [max_pae, gamma_real, gamma_imag]).
                  Returns an empty list if the data is not found or simulation failed.
        """
        graph_name = getattr(self, 'name', 'Unknown Graph')
        logger.info(f"├── Fetching data from graph: '{graph_name}', Measurement: '{measurement_name}'")

        try:
            target_meas = None

            for i in range(1, self.awr_graph.Measurements.Count + 1):
                meas = self.awr_graph.Measurements.Item(i)
                if measurement_name in meas.Name:
                    target_meas = meas
                    break

            if target_meas is None or target_meas.XPointCount < 1:
                logger.error(f"│   └── Measurement '{measurement_name}' not found or contains no data.")
                return []

            y_dimensions = target_meas.YDataDim
            all_y_values = []

            # Collect data for all Y dimensions
            for dim in range(1, y_dimensions + 1):
                all_y_values.append(target_meas.YValue(1, dim))

            logger.info("│   └── Data extraction completed successfully.")
            return all_y_values

        except Exception as e:
            logger.error(f"│   └── An error occurred during data extraction: {e}")
            return []

if __name__ == "__main__":
    logger.info("├── Starting standalone test sequence for graph.py")
    try:
        test_app = mwoffice.CMWOffice()
        graph_service = Graph(test_app)

        test_graph_name = "Automated Test Rectangular"
        graph_service.create_new_graph(test_graph_name, GraphType.RECTANGULAR)

        logger.info("└── Test execution sequence completed successfully.")
    except Exception as ex:
        logger.critical(f"└── Test execution failed: {ex}")
        sys.exit(1)