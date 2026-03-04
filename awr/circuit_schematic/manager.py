"""
manager.py (Circuit Schematic Domain)
Handles all API interactions related to schematic configurations,
elements, routing, and frequency settings.
Strictly adheres to the professional coding standards.
"""

from typing import Dict, Any, Union, List, Optional
from awr.circuit_schematic.element import Element
from awr.circuit_schematic.schematic import Schematic
from core.logger import logger

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

    def replace_element(self, schematic_name: str, target_designator: str, node_mapping: Dict[int, Union[int, List[int]]], library_path: Optional[str] = None, element_name: Optional[str] = None) -> bool:
        """
        Orchestrates the sequence of replacing an element and applying custom wiring maps.
        """
        logger.info(f"├── Initiating macro sequence: Replace & Rewire for '{target_designator}'")

        old_element = self.element_service.find_element(schematic_name, target_designator)
        if not old_element:
            logger.error(f"└── Sequence aborted: Target element '{target_designator}' not found.")
            return False

        center_x = old_element.x
        center_y = old_element.y
        old_nodes = self.element_service.get_element_node_positions(schematic_name, target_designator)

        if not self.element_service.delete_element(schematic_name, target_designator):
            logger.error("└── Sequence aborted: Failed to delete the target element.")
            return False

        # 3. Add the New Element
        new_element = None
        if library_path:
            logger.debug(f"│   ├── Attempting instantiation via library path: {library_path}")
            new_element = self.element_service.add_element(
                schematic_name, center_x, center_y, library_path=library_path
            )
        elif element_name:
            logger.debug(f"│   ├── Attempting instantiation via standard name: {element_name}")
            new_element = self.element_service.add_element(
                schematic_name, center_x, center_y, element_name=element_name
            )

        if not new_element:
            logger.error("└── Sequence aborted: No valid source provided or instantiation failed.")
            return False

        new_nodes = self.element_service.get_element_node_positions(schematic_name, new_element.Name)

        old_nodes_dict = {n["PinNumber"]: n for n in old_nodes}
        new_nodes_dict = {n["PinNumber"]: n for n in new_nodes}

        logger.info(f"├── Applying node wiring matrix for '{new_element.Name}'...")
        wire_count = 0

        for old_pin, target_pins in node_mapping.items():
            if old_pin not in old_nodes_dict:
                logger.warning(f"│   ├── Original pin {old_pin} does not exist. Skipping.")
                continue

            o_node = old_nodes_dict[old_pin]

            if not isinstance(target_pins, list):
                target_pins = [target_pins]

            for new_pin in target_pins:
                if new_pin not in new_nodes_dict:
                    logger.warning(f"│   ├── Target pin {new_pin} does not exist on new element. Skipping.")
                    continue

                n_node = new_nodes_dict[new_pin]

                if (o_node["x"] != n_node["x"]) or (o_node["y"] != n_node["y"]):
                    # Artık doğrudan Manager içindeki kendi add_wire fonksiyonunu çağırıyoruz!
                    if self.add_wire(schematic_name, o_node["x"], o_node["y"], n_node["x"], n_node["y"]):
                        wire_count += 1
                else:
                    logger.debug(f"│   ├── Pins perfectly overlap (Old:{old_pin} -> New:{new_pin}). Wiring bypassed.")

        logger.info(f"└── Replacement sequence finalized. Total wires drawn: {wire_count}")
        return True

    def set_frequency(self, schematic_name: str, freq: Union[float, List[float]]) -> None:
        self.schematic_service.set_frequency(schematic_name, freq)