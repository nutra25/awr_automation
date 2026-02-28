"""
add_element.py
Provides atomic functionality to instantiate a standard circuit element (e.g., RES, CAP, PORT)
directly by its name within an AWR schematic.
Strictly adheres to the tree-branch logging hierarchy.
"""

import pyawr.mwoffice as mwoffice
import sys
from typing import Any, Optional

from logger.logger import LOGGER


def add_element(app: Any, schematic_name: str, element_name: str, x_pos: float, y_pos: float) -> Optional[Any]:
    """
    Adds a standard circuit element to the specified schematic at given coordinates.

    Args:
        app: The active AWR MWOffice COM application instance.
        schematic_name (str): Name of the target schematic.
        element_name (str): The name of the element to add (e.g., 'RES' for resistor).
        x_pos (float): X coordinate for placement.
        y_pos (float): Y coordinate for placement.

    Returns:
        The instantiated COM element object, or None if the operation fails.
    """
    LOGGER.info(f"├── Instantiating standard element '{element_name}' at ({x_pos}, {y_pos}) in '{schematic_name}'")

    try:
        schematic = app.Project.Schematics(schematic_name)
        # Add method is used for standard elements instead of AddLibraryElement
        new_element = schematic.Elements.Add(element_name, x_pos, y_pos)

        LOGGER.info(f"└── Successfully added element. Assigned Name: '{new_element.Name}'")
        return new_element
    except Exception as e:
        LOGGER.error(f"└── Failed to add standard element. Details: {e}")
        return None


if __name__ == "__main__":
    LOGGER.info("Starting standalone test sequence for add_element.py")
    try:
        test_app = mwoffice.CMWOffice()
        # Ensure the target schematic exists in the active project before running
        target_schematic = "VDS40_Load_Pull"
        test_element = "RES"

        add_element(test_app, target_schematic, test_element, 0, 0)
        LOGGER.info("└── Test execution sequence completed.")
    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed: {ex}")
        sys.exit(1)