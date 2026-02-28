"""
find_element.py
Provides isolated functionality to locate specific elements within an AWR schematic.
Returns the element COM object for subsequent operations, ensuring modularity.
Adheres to the strict tree-branch logging hierarchy.
"""

import pyawr.mwoffice as mwoffice
import sys
from typing import Optional, Any

from logger.logger import LOGGER

def find_schematic_element(
        app: Any,
        schematic_name: str,
        target_designator: str,
        allow_partial_match: bool = False
) -> Optional[Any]:
    """
    Locates a specified element from a given schematic by Name or ID.

    Args:
        app: The active AWR MWOffice COM application instance.
        schematic_name (str): The exact name of the target schematic.
        target_designator (str): The name or ID of the element to be located.
        allow_partial_match (bool): If True, matches the designator as a substring.

    Returns:
        The COM object of the identified element, or None if not found.
    """
    LOGGER.info(f"├── Initiating element search sequence: Schematic='{schematic_name}', Target='{target_designator}'")

    try:
        active_schematic = app.Project.Schematics(schematic_name)
    except Exception:
        LOGGER.error(f"└── Failed to locate schematic: '{schematic_name}'. Search sequence aborted.")
        return None

    for candidate_element in active_schematic.Elements:
        element_identifier = candidate_element.Name
        is_match = False

        if allow_partial_match:
            if target_designator in element_identifier:
                is_match = True
        else:
            if target_designator == element_identifier:
                is_match = True

        # Attempt to match via "ID" parameter if the name does not match
        if not is_match and candidate_element.Parameters.Exists("ID"):
            element_id_value = candidate_element.Parameters("ID").ValueAsString
            if element_id_value == target_designator:
                is_match = True

        if is_match:
            LOGGER.debug(f"│   ├── Target element identified successfully: {candidate_element.Name}")
            LOGGER.info(f"└── Search sequence completed.")
            return candidate_element

    LOGGER.warning(f"└── Element '{target_designator}' could not be found in schematic '{schematic_name}'.")
    return None


# Standalone Test Execution Block
if __name__ == "__main__":
    LOGGER.info("Starting standalone test sequence for find_element.py module.")

    try:
        test_app = mwoffice.CMWOffice()
        LOGGER.info("├── Successfully connected to AWR Microwave Office for testing.")

        test_schematic = "Load_Pull_Template"
        test_target = "CFH1"

        element = find_schematic_element(test_app, test_schematic, test_target)

        if element:
            LOGGER.info(f"└── Test successful. Element resolved: {element.Name}")
        else:
            LOGGER.warning("└── Test completed. Element was not resolved.")

    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed. Details: {ex}")
        sys.exit(1)