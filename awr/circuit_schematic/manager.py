"""
manager.py (Circuit Schematic Domain)
Handles all API interactions related to schematic configurations,
elements, and frequency settings.
"""

from typing import Dict, Any, Union, List, Optional

from awr.circuit_schematic.awr_configure_schematic_element import configure_schematic_element
from awr.circuit_schematic.awr_configure_schematic_rf_frequency import configure_schematic_rf_frequency
from awr.circuit_schematic.delete_element import delete_schematic_element
from awr.circuit_schematic.find_element import find_schematic_element

class CircuitSchematicManager:
    """
    Manages AWR Schematic operations, ensuring domain encapsulation.
    """
    def __init__(self, app):
        self.app = app

    def configure_element(self, schematic_name: str, element_name: str, params: Dict[str, Any]) -> None:
        """Configures specific element parameters within a given schematic context."""
        configure_schematic_element(self.app, schematic_name, element_name, params)

    def add_element(self, schematic_name: str, element_type: str, x_pos: int, y_pos: int) -> None:
        """Placeholder for dynamic element addition logic."""
        pass

    def find_element(self, schematic_name: str, target_designator: str, allow_partial_match: bool = False) -> Optional[Any]:
        """
        Locates and returns the COM object of a specified element.
        """
        return find_schematic_element(self.app, schematic_name, target_designator, allow_partial_match)

    def delete_element(self, schematic_name: str, target_designator: str, allow_partial_match: bool = False) -> bool:
        """Locates and removes a specified element from the defined schematic."""
        return delete_schematic_element(self.app, schematic_name, target_designator, allow_partial_match)

    def set_frequency(self, schematic_name: str, freq: Union[float, List[float]]) -> None:
        """Updates the system simulation frequency for a specific schematic."""
        configure_schematic_rf_frequency(self.app, schematic_name, freq)