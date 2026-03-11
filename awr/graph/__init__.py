import re
from enum import Enum
from typing import Union, Any

import pyawr.mwoffice as mwoffice
from awr.awr_component import AWRComponent
from .marker import Marker
from .measurement import Measurement

class GraphType(Enum):
    RECTANGULAR = mwoffice.mwGraphType.mwGT_Rectangular
    RECTANGULAR_COMPLEX = mwoffice.mwGraphType.mwGT_RectangularComplex
    SMITH_CHART = mwoffice.mwGraphType.mwGT_SmithChart
    POLAR = mwoffice.mwGraphType.mwGT_Polar
    HISTOGRAM = mwoffice.mwGraphType.mwGT_Histogram
    TABULAR = mwoffice.mwGraphType.mwGT_Tabular
    ANTENNA = mwoffice.mwGraphType.mwGT_Antenna
    THREE_DIMENSIONAL = mwoffice.mwGraphType.mwGT_ThreeDim
    CONSTELLATION = mwoffice.mwGraphType.mwGT_Constellation

class MarkerDisplayFormat(Enum):
    MAGNITUDE_ANGLE = mwoffice.mwGraphMarkerFormat.mwGMF_MagnitudeAngle
    REAL_IMAGINARY = mwoffice.mwGraphMarkerFormat.mwGMF_RealImaginary
    DB_MAGNITUDE_ANGLE = mwoffice.mwGraphMarkerFormat.mwGMF_DbMagnitudeAngle

class Graph(AWRComponent):
    def __init__(self, awr):
        super().__init__(awr)
        self.measurement = Measurement(self)
        self.marker = Marker(self)

    def find_graph(self, graph_name) -> bool:
        graphs = self.app.Project.Graphs
        for i in range(1, graphs.Count + 1):
            if graphs.Item(i).Name == graph_name:
                return True
        return False

    def create_new_graph(self, graph_name: str, graph_type: GraphType) -> bool:

        self.logger.info(f"├── Attempting to create new graph: '{graph_name}' (Type: {graph_type.name})")

        if not re.match(r'^[A-Za-z0-9_ ]+$', graph_name):
            self.logger.error("└── Invalid graph name. Only alphanumeric characters, underscores, and spaces are permitted.")
            return False

        try:
            graphs = self.app.Project.Graphs

            for i in range(1, graphs.Count + 1):
                if graphs.Item(i).Name == graph_name:
                    self.logger.warning(f"└── Graph '{graph_name}' already exists. Creation aborted.")
                    return False

            graphs.Add(graph_name, graph_type.value)
            self.logger.info(f"└── Successfully created graph: '{graph_name}'")
            return True

        except Exception as e:
            self.logger.error(f"└── Failed to create graph '{graph_name}'. Exception: {e}")
            return False

    def set_graph_marker_display_format(self, graph_name: str, display_format: MarkerDisplayFormat) -> bool:

        self.logger.info(f"├── Attempting to set marker format for graph '{graph_name}' to '{display_format.name}'")

        try:
            if not self.app.Project.Graphs.Exists(graph_name):
                self.logger.error(f"└── Target graph '{graph_name}' does not exist.")
                return False

            graph = self.app.Project.Graphs(graph_name)
            graph.Markers.Options.DisplayFormat = display_format.value

            self.logger.info(f"└── Successfully updated marker format for '{graph_name}'.")
            return True

        except Exception as e:
            self.logger.error(f"└── Failed to update marker format for '{graph_name}'. Exception: {e}")
            return False

    def toggle_measurements(self, target_graph: Union[str, Any], enable: bool) -> bool:

        if isinstance(target_graph, str):
            if not self.app.Project.Graphs.Exists(target_graph):
                self.logger.error(f"│   └── Target graph '{target_graph}' does not exist for toggle operation.")
                return False

            graph_obj = self.app.Project.Graphs(target_graph)
        else:
            graph_obj = target_graph

        state_str = "Enabling" if enable else "Disabling"

        self.logger.debug(f"│   ├── {state_str} measurements for graph '{graph_obj.Name}'...")

        try:
            for meas in graph_obj.Measurements:
                meas.Enabled = enable
            return True

        except Exception as e:
            self.logger.error(f"│   └── Failed to toggle measurements for graph '{graph_obj.Name}': {e}")
            return False

if __name__ == "__main__":
    pass