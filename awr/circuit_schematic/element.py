"""
element.py
"""

import sys
from typing import Any, Optional, Dict, Union, List
import pyawr.mwoffice as mwoffice

from core.logger import logger

class Element:
    """
    Service class managing circuit schematic elements operations.
    """
    def __init__(self, app: Any):
        """
        Initializes the Element operations class.

        Args:
            app (Any): The active AWR MWOffice COM application instance.
        """
        self.app = app

    def add_element(
            self,
            schematic_name: str,
            x_pos: float,
            y_pos: float,
            element_name: Optional[str] = None,
            library_path: Optional[str] = None
    ) -> Optional[Any]:
        """
        Adds a circuit element to the specified schematic at given coordinates.
        Instantiates from a library if library_path is provided, otherwise adds a standard element by element_name.
        """
        if library_path:
            logger.info(f"├── Instantiating library element at ({x_pos}, {y_pos}) in '{schematic_name}'")
        elif element_name:
            logger.info(
                f"├── Instantiating standard element '{element_name}' at ({x_pos}, {y_pos}) in '{schematic_name}'")
        else:
            logger.error("└── Failed to add element: Must provide either 'element_name' or 'library_path'.")
            return None

        try:
            schematic = self.app.Project.Schematics(schematic_name)

            if library_path:
                new_element = schematic.Elements.AddLibraryElement(library_path, x_pos, y_pos)
            else:
                new_element = schematic.Elements.Add(element_name, x_pos, y_pos)

            logger.info(f"└── Successfully added element. Assigned Name: '{new_element.Name}'")
            return new_element
        except Exception as e:
            logger.error(f"└── Failed to add element. Details: {e}")
            return None

    def find_element(self, schematic_name: str, target_designator: str, allow_partial_match: bool = False) -> Union[Any, List[Any], None]:
        """Locates a specified element from a given schematic by Name or ID."""
        logger.info(f"├── Initiating element search sequence: Schematic='{schematic_name}', Target='{target_designator}'")
        logger.debug(f"│   ├── Mode: {'Partial Match (Bulk)' if allow_partial_match else 'Exact Match (Single)'}")

        try:
            active_schematic = self.app.Project.Schematics(schematic_name)
        except Exception:
            logger.error(f"└── Failed to locate schematic: '{schematic_name}'. Search sequence aborted.")
            return [] if allow_partial_match else None

        matched_elements = []

        for candidate_element in active_schematic.Elements:
            element_identifier = candidate_element.Name
            is_match = False

            if allow_partial_match:
                if target_designator in element_identifier:
                    is_match = True
            else:
                if target_designator == element_identifier:
                    is_match = True

            if not is_match and candidate_element.Parameters.Exists("ID"):
                element_id_value = candidate_element.Parameters("ID").ValueAsString
                if allow_partial_match:
                    if target_designator in element_id_value:
                        is_match = True
                else:
                    if element_id_value == target_designator:
                        is_match = True

            if is_match:
                if not allow_partial_match:
                    logger.debug(f"│   ├── Exact target element identified: {candidate_element.Name}")
                    logger.info(f"└── Search sequence completed successfully.")
                    return candidate_element
                else:
                    matched_elements.append(candidate_element)

        if allow_partial_match:
            if matched_elements:
                logger.info(f"└── Search sequence completed. Found {len(matched_elements)} matching element(s).")
                return matched_elements
            else:
                logger.warning(f"└── No elements found containing the substring '{target_designator}'.")
                return []

        logger.warning(f"└── Exact element '{target_designator}' could not be found in '{schematic_name}'.")
        return None

    def configure_element(self, schematic_name: str, target_designator: str, parameter_map: Dict[str, Any], allow_partial_match: bool = False) -> bool:
        """Configures specific parameters of a target element within an AWR schematic."""
        logger.info(f"├── Initiating configuration sequence for '{target_designator}' in '{schematic_name}'")

        identified_element = self.find_element(schematic_name, target_designator, allow_partial_match)

        if identified_element is None:
            logger.warning(f"└── Configuration aborted: Target element reference could not be resolved.")
            return False

        element_name = identified_element.Name
        param_items = list(parameter_map.items())
        total_params = len(param_items)
        updates_made = 0

        logger.debug(f"├── Applying parameters to '{element_name}'...")

        for index, (param_key, param_value) in enumerate(param_items):
            is_last_item = (index == total_params - 1)
            tree_char = "└──" if is_last_item else "├──"

            if identified_element.Parameters.Exists(param_key):
                target_parameter = identified_element.Parameters(param_key)
                old_value = target_parameter.ValueAsString

                try:
                    target_parameter.ValueAsString = str(param_value)
                    logger.info(f"│   {tree_char} {param_key}: [{old_value}] -> [{param_value}]")
                    updates_made += 1
                except Exception as e:
                    logger.error(f"│   {tree_char} Failed to update '{param_key}'. Exception: {e}")
            else:
                logger.warning(f"│   {tree_char} Parameter '{param_key}' is missing on element '{element_name}'.")

        if updates_made > 0:
            logger.info(f"└── Successfully configured {updates_made} parameter(s) for '{element_name}'.")
            return True
        else:
            logger.warning(f"└── No parameters were updated for '{element_name}'.")
            return False

    def delete_element(self, schematic_name: str, target_designator: str, allow_partial_match: bool = False) -> bool:
        """Deletes a specified element from a given schematic after resolving its reference."""
        logger.info(f"├── Initiating deletion sequence for target '{target_designator}' in '{schematic_name}'")

        identified_element = self.find_element(schematic_name, target_designator, allow_partial_match)

        if identified_element is None:
            logger.warning(f"└── Deletion aborted: Target element reference could not be resolved.")
            return False

        element_name = identified_element.Name

        try:
            delete_success = identified_element.Delete()

            if delete_success:
                logger.info(f"└── Successfully DELETED element '{element_name}'.")
                return True
            else:
                logger.error(f"└── API returned False while attempting to delete '{element_name}'.")
                return False

        except Exception as e:
            logger.error(f"└── Encountered an exception during the deletion of '{element_name}': {e}")
            return False

    def get_element_node_positions(self, schematic_name: str, target_designator: str, allow_partial_match: bool = False) -> List[Dict[str, Any]]:
        """Extracts the X and Y coordinates of all nodes for a specified element."""
        logger.info(f"├── Initiating node extraction sequence for '{target_designator}' in '{schematic_name}'")

        identified_element = self.find_element(schematic_name, target_designator, allow_partial_match)

        if identified_element is None:
            logger.warning(f"└── Extraction aborted: Target element reference could not be resolved.")
            return []

        node_coordinates = []

        for pin_index, node in enumerate(identified_element.Nodes, start=1):
            net_num = node.NodeNumber
            x_pos = node.x
            y_pos = node.y

            node_coordinates.append({
                "PinNumber": pin_index,
                "NetNumber": net_num,
                "x": x_pos,
                "y": y_pos
            })

            logger.debug(f"│   ├── Extracted Pin {pin_index} (Assigned to Net {net_num}): X={x_pos}, Y={y_pos}")

        logger.info(f"└── Successfully extracted {len(node_coordinates)} node(s) for '{identified_element.Name}'.")
        return node_coordinates

if __name__ == "__main__":
    logger.info("├── Starting standalone test sequence for element.py")
    try:
        test_app = mwoffice.CMWOffice()
        element_service = Element(test_app)

        test_schematic = "Load_Pull_Template"
        test_target = "PORT_PS1"

        res = element_service.find_element(test_schematic, test_target, allow_partial_match=True)
        if res:
             logger.info(f"│   ├── Test find_element returned {len(res) if isinstance(res, list) else 1} items.")

        logger.info("└── Test execution sequence completed successfully.")
    except Exception as ex:
        logger.critical(f"└── Test execution failed: {ex}")
        sys.exit(1)