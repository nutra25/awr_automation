# AWR Automation Modules
import pyawr.mwoffice as mwoffice
from awr.awr_get_marker_value import get_marker_value
from awr.awr_configure_schematic_element import configure_schematic_element
from awr.awr_loadpull_wizard import run_loadpull_wizard
from awr.awr_configure_schematic_rf_frequency import configure_schematic_rf_frequency
from awr.awr_get_broadband_contours import extract_graph_data

from typing import List, Dict, Any, Union
from config import SCHEMATIC_NAME
import re

from shapely.geometry import Polygon

class AWRDriver:
    """
    Static interface wrapper for AWR Microwave Office API operations.
    Isolates direct API calls from the main simulation logic.
    """

    def __init__(self):
        """Connecting to AWR"""
        try:
            self.app = mwoffice.CMWOffice()
        except Exception as e:
            raise

    def configure_element(self, element_name: str, params: Dict[str, Any]) -> None:
        """Configures a schematic element with the provided parameters."""
        configure_schematic_element(
            self.app,
            schematic_title=SCHEMATIC_NAME,
            target_designator=element_name,
            parameter_map=params,
        )

    def set_frequency(self, freq: Union[float, List[float]]) -> None:
        """Updates the system simulation frequency."""
        configure_schematic_rf_frequency(
            self.app,
            schematic_name=SCHEMATIC_NAME,
            frequencies=freq
        )

    def get_marker_data(self, graph: str, marker: str, toggle_enable: bool = False) -> List[float]:
        """
        Retrieves numerical data from a graph marker.

        Returns:
            List[float]: Extracted numerical values (e.g., [Mag, Ang]).
                         Returns a list of zeros if retrieval fails.
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

        # Extract floating point numbers using regex
        numbers = re.findall(r"-?\d+\.?\d*", raw_output)
        return [float(n) for n in numbers]

    def run_wizard(self, options: Dict[str, Any]) -> None:
        """Triggers the Load Pull Wizard with the specified configuration."""
        run_loadpull_wizard(self.app, options)

    def get_broadband_contours(self, graph_name: str) -> Dict[float, List[Dict[str, Any]]]:
        return extract_graph_data(self.app, graph_name)