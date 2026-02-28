"""
manager.py (Circuit Schematic Domain)
Handles all API interactions related to schematic configurations,
elements, routing, and frequency settings.
"""

from typing import Dict, Any, Union, List, Optional

from awr.circuit_schematic.configure_schematic_element import configure_schematic_element
from awr.circuit_schematic.configure_schematic_rf_frequency import configure_schematic_rf_frequency
from awr.circuit_schematic.delete_element import delete_schematic_element
from awr.circuit_schematic.find_element import find_schematic_element
from awr.circuit_schematic.add_library_element import add_library_element
from awr.circuit_schematic.add_element import add_element  # Imported the new standard element addition logic
from awr.circuit_schematic.add_wire import add_wire
from awr.circuit_schematic.replace_element import replace_element
from awr.circuit_schematic.get_element_node_positions import get_element_node_positions

class CircuitSchematicManager:
    """
    Manages AWR Schematic operations, ensuring domain encapsulation.
    """
    def __init__(self, app):
        self.app = app

    def configure_element(self, schematic_name: str, element_name: str, params: Dict[str, Any]) -> bool:
        return configure_schematic_element(self.app, schematic_name, element_name, params)

    def find_element(self, schematic_name: str, target_designator: str, allow_partial_match: bool = False) -> Union[Any, List[Any], None]:
        return find_schematic_element(self.app, schematic_name, target_designator, allow_partial_match)

    def delete_element(self, schematic_name: str, target_designator: str, allow_partial_match: bool = False) -> bool:
        return delete_schematic_element(self.app, schematic_name, target_designator, allow_partial_match)

    def get_node_positions(self, schematic_name: str, target_designator: str) -> List[Dict[str, Any]]:
        return get_element_node_positions(self.app, schematic_name, target_designator)

    def add_library_element(self, schematic_name: str, library_path: str, x: float, y: float) -> Optional[Any]:
        """Adds an element from the AWR Library path."""
        return add_library_element(self.app, schematic_name, library_path, x, y)

    def add_element(self, schematic_name: str, element_name: str, x: float, y: float) -> Optional[Any]:
        """Adds a standard circuit element (e.g., RES, CAP) by its name."""
        return add_element(self.app, schematic_name, element_name, x, y)

    def add_wire(self, schematic_name: str, x1: float, y1: float, x2: float, y2: float) -> bool:
        return add_wire(self.app, schematic_name, x1, y1, x2, y2)

    def replace_element(self, schematic_name: str, target: str, mapping: Dict[int, Union[int, List[int]]],
                        library_path: str = None, element_name: str = None) -> bool:
        """Executes the macro sequence to replace an element using either library path or standard name."""
        return replace_element(self.app, schematic_name, target, mapping, library_path, element_name)

    def set_frequency(self, schematic_name: str, freq: Union[float, List[float]]) -> None:
        configure_schematic_rf_frequency(self.app, schematic_name, freq)