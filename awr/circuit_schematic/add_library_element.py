"""
add_library_element.py
Provides atomic functionality to instantiate a new element from an AWR library path.
Strictly adheres to the tree-branch logging hierarchy.
"""

import pyawr.mwoffice as mwoffice
import sys
from typing import Any, Optional

from logger.logger import LOGGER


def add_library_element(app: Any, schematic_name: str, library_path: str, x_pos: float, y_pos: float) -> Optional[Any]:
    """
    Adds a new element from the library to the specified schematic at given coordinates.

    Args:
        app: The active AWR MWOffice COM application instance.
        schematic_name (str): Target schematic name.
        library_path (str): Absolute or relative path to the library element.
        x_pos (float): X coordinate for instantiation.
        y_pos (float): Y coordinate for instantiation.

    Returns:
        The instantiated COM element object, or None if failed.
    """
    LOGGER.info(f"├── Instantiating library element at ({x_pos}, {y_pos}) in '{schematic_name}'")

    try:
        schematic = app.Project.Schematics(schematic_name)
        new_element = schematic.Elements.AddLibraryElement(library_path, x_pos, y_pos)
        LOGGER.info(f"└── Successfully added library element. Assigned Name: '{new_element.Name}'")
        return new_element
    except Exception as e:
        LOGGER.error(f"└── Failed to add library element. Details: {e}")
        return None


if __name__ == "__main__":
    LOGGER.info("Starting standalone test sequence for add_library_element.py")
    try:
        test_app = mwoffice.CMWOffice()
        # Ensure the schematic and path exist before testing
        test_path = "BP:\\Circuit Elements\\Libraries\\*MA_RFP -- v0.0.2.5\\GaN Product\\CGHV1F006S"
        add_library_element(test_app, "Load_Pull_Template", test_path, 0, 0)
        LOGGER.info("└── Test execution sequence completed.")
    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed: {ex}")
        sys.exit(1)