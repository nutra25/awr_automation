"""
manager.py (Circuit Schematic Domain)
Handles all API interactions related to schematic configurations,
elements, routing, and frequency settings.
Strictly adheres to the professional coding standards.
"""

from typing import Dict, Any, Union, List, Optional
from awr.circuit_schematic.element import Element
from awr.circuit_schematic.schematic import Schematic


class CircuitSchematicManager:
    """
    Manages AWR Schematic operations, ensuring domain encapsulation.
    Acts as a facade utilizing specific domain sub-services (Element, Schematic).
    """
    def __init__(self, app: Any):
        """
        Initializes the CircuitSchematicManager and its underlying service objects.

        Args:
            app (Any): The active AWR MWOffice COM application instance.
        """
        self.app = app

        # Instantiate encapsulated domain services
        self.element_service = Element(self.app)
        self.schematic_service = Schematic(self.app)

    def configure_element(self, schematic_name: str, element_name: str, params: Dict[str, Any]) -> bool:
        return self.element_service.configure_element(schematic_name, element_name, params)

    def find_element(self, schematic_name: str, target_designator: str, allow_partial_match: bool = False) -> Union[Any, List[Any], None]:
        return self.element_service.find_element(schematic_name, target_designator, allow_partial_match)

    def delete_element(self, schematic_name: str, target_designator: str, allow_partial_match: bool = False) -> bool:
        return self.element_service.delete_element(schematic_name, target_designator, allow_partial_match)

    def get_element_node_positions(self, schematic_name: str, target_designator: str) -> List[Dict[str, Any]]:
        return self.element_service.get_element_node_positions(schematic_name, target_designator)

    def add_element(self, schematic_name: str, x_pos: float, y_pos: float,
                    element_name: Optional[str] = None, library_path: Optional[str] = None) -> Optional[Any]:
        """
        Adds a standard circuit element or a library element to the specified schematic.
        Delegates the creation logic based on provided arguments.
        """
        return self.element_service.add_element(schematic_name, x_pos, y_pos, element_name, library_path)

    def add_wire(self, schematic_name: str, x1: float, y1: float, x2: float, y2: float) -> bool:
        return self.schematic_service.add_wire(schematic_name, x1, y1, x2, y2)

    def replace_element(self, schematic_name: str, target: str, mapping: Dict[int, Union[int, List[int]]],
                        library_path: str = None, element_name: str = None) -> bool:
        """Executes the macro sequence to replace an element using either library path or standard name."""
        return self.element_service.replace_element(schematic_name, target, mapping, library_path, element_name)

    def set_frequency(self, schematic_name: str, freq: Union[float, List[float]]) -> None:
        self.schematic_service.set_frequency(schematic_name, freq)