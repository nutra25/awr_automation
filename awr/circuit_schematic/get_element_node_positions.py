"""
get_element_node_positions.py
Provides functionality to extract node coordinates from a specified schematic element.
Differentiates between Local Pin Index (1, 2, 3) and Global Electrical Net Node.
Delegates search logic to the find_element module to comply with SRP.
Strictly adheres to the tree-branch logging hierarchy.
"""

import pyawr.mwoffice as mwoffice
import sys
from typing import List, Dict, Any

from logger.logger import LOGGER
from awr.circuit_schematic.find_element import find_schematic_element


def get_element_node_positions(
        app: Any,
        schematic_name: str,
        target_designator: str,
        allow_partial_match: bool = False
) -> List[Dict[str, Any]]:
    """
    Extracts the X and Y coordinates of all nodes for a specified element.

    Args:
        app: The active AWR MWOffice COM application instance.
        schematic_name (str): The exact name of the target schematic.
        target_designator (str): The name or ID of the element to be located.
        allow_partial_match (bool): If True, matches the designator as a substring.

    Returns:
        A list of dictionaries containing 'PinNumber' (Local), 'NetNumber' (Global),
        and spatial 'x', 'y' coordinates.
    """
    LOGGER.info(f"├── Initiating node extraction sequence for '{target_designator}' in '{schematic_name}'")

    identified_element = find_schematic_element(app, schematic_name, target_designator, allow_partial_match)

    if identified_element is None:
        LOGGER.warning(f"└── Extraction aborted: Target element reference could not be resolved.")
        return []

    node_coordinates = []

    # Iterate through the nodes utilizing enumeration for Local Pin Index (1-based)
    for pin_index, node in enumerate(identified_element.Nodes, start=1):
        net_num = node.NodeNumber  # The global electrical node ID
        x_pos = node.x
        y_pos = node.y

        node_coordinates.append({
            "PinNumber": pin_index,
            "NetNumber": net_num,
            "x": x_pos,
            "y": y_pos
        })

        LOGGER.debug(f"│   ├── Extracted Pin {pin_index} (Assigned to Net {net_num}): X={x_pos}, Y={y_pos}")

    LOGGER.info(f"└── Successfully extracted {len(node_coordinates)} node(s) for '{identified_element.Name}'.")
    return node_coordinates


# Standalone Test Execution Block
if __name__ == "__main__":
    LOGGER.info("Starting standalone test sequence for get_element_node_positions.py module.")

    try:
        test_app = mwoffice.CMWOffice()
        LOGGER.info("├── Successfully connected to AWR Microwave Office for testing.")

        test_schematic = "Load_Pull_Template"
        test_target = "CURTICE3.CFH1"

        coordinates = get_element_node_positions(test_app, test_schematic, test_target)

        if coordinates:
            LOGGER.info("└── Test execution sequence completed successfully.")
        else:
            LOGGER.warning("└── Test execution completed, but no coordinates were extracted.")

    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed. Details: {ex}")
        sys.exit(1)