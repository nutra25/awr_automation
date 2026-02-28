"""
replace_element.py
Macro-orchestrator that replaces an existing schematic element with a new one
from a library and rewires the nodes based on a specified mapping.
Supports both one-to-one and one-to-many node wiring matrices.
"""

import pyawr.mwoffice as mwoffice
import sys
from typing import Dict, Any, Union, List

from logger.logger import LOGGER

# Importing specialized atomic modules
from awr.circuit_schematic.find_element import find_schematic_element
from awr.circuit_schematic.get_element_node_positions import get_element_node_positions
from awr.circuit_schematic.delete_element import delete_schematic_element
from awr.circuit_schematic.add_library_element import add_library_element
from awr.circuit_schematic.add_wire import add_wire


def replace_element(
        app: Any,
        schematic_name: str,
        target_designator: str,
        library_path: str,
        node_mapping: Dict[int, Union[int, List[int]]]
) -> bool:
    """
    Orchestrates the sequence of extracting data, deleting the old element,
    instantiating the new library element, and applying custom wiring maps.
    Supports list-based assignments for one-to-many pin connectivity.
    """
    LOGGER.info(f"├── Initiating macro sequence: Replace & Rewire for '{target_designator}'")

    # 1. Resolve Target and Extract Core Data
    old_element = find_schematic_element(app, schematic_name, target_designator)
    if not old_element:
        LOGGER.error("└── Sequence aborted: Target element not found.")
        return False

    center_x = old_element.x
    center_y = old_element.y
    old_nodes = get_element_node_positions(app, schematic_name, target_designator)

    # 2. Delete the Old Element
    if not delete_schematic_element(app, schematic_name, target_designator):
        LOGGER.error("└── Sequence aborted: Failed to delete the target element.")
        return False

    # 3. Add the New Library Element
    new_element = add_library_element(app, schematic_name, library_path, center_x, center_y)
    if not new_element:
        LOGGER.error("└── Sequence aborted: Failed to instantiate new element.")
        return False

    # 4. Extract New Element's Nodes
    new_nodes = get_element_node_positions(app, schematic_name, new_element.Name)

    # Organize nodes by their local PinNumber for O(1) lookup
    old_nodes_dict = {n["PinNumber"]: n for n in old_nodes}
    new_nodes_dict = {n["PinNumber"]: n for n in new_nodes}

    # 5. Execute Wiring Strategy
    LOGGER.info(f"├── Applying node wiring matrix for '{new_element.Name}'...")
    wire_count = 0

    for old_pin, target_pins in node_mapping.items():
        if old_pin not in old_nodes_dict:
            LOGGER.warning(f"│   ├── Original pin {old_pin} does not exist. Skipping.")
            continue

        o_node = old_nodes_dict[old_pin]

        # Normalize target_pins to a list to natively support one-to-many definitions
        if not isinstance(target_pins, list):
            target_pins = [target_pins]

        for new_pin in target_pins:
            if new_pin not in new_nodes_dict:
                LOGGER.warning(f"│   ├── Target pin {new_pin} does not exist on new element. Skipping.")
                continue

            n_node = new_nodes_dict[new_pin]

            # Draw wire if coordinates differ
            if (o_node["x"] != n_node["x"]) or (o_node["y"] != n_node["y"]):
                if add_wire(app, schematic_name, o_node["x"], o_node["y"], n_node["x"], n_node["y"]):
                    wire_count += 1
            else:
                LOGGER.debug(f"│   ├── Pins perfectly overlap (Old:{old_pin} -> New:{new_pin}). Wiring bypassed.")

    LOGGER.info(f"└── Replacement sequence finalized. Total wires drawn: {wire_count}")
    return True


if __name__ == "__main__":
    LOGGER.info("Starting standalone test sequence for replace_element.py")
    try:
        test_app = mwoffice.CMWOffice()
        test_schematic = "Load_Pull_Template"
        test_target = "CFH1"
        test_lib = "BP:\\Circuit Elements\\Libraries\\*MA_RFP -- v0.0.2.5\\GaN Product\\CGHV1F006S"

        # Test Case: Demonstrating robust one-to-many wiring map
        test_map = {
            1: 1,                 # Old 1 to New 1 (Single)
            2: 2,               # Old 2 to New 2 (List format)
            3: [3, 4, 5, 6, 7]       # Old 3 to New 3, 4, 5, 6 (One-to-Many)
        }

        replace_element(test_app, test_schematic, test_target, test_lib, test_map)
    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed: {ex}")
        sys.exit(1)