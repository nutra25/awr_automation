"""
delete_element.py
Provides functionality to safely delete specific elements from an AWR schematic.
Delegates the search logic to the find_element module to comply with SRP.
"""

import pyawr.mwoffice as mwoffice
import sys
from typing import Any

from logger.logger import LOGGER

from awr.circuit_schematic.find_element import find_schematic_element

def delete_schematic_element(
        app: Any,
        schematic_name: str,
        target_designator: str,
        allow_partial_match: bool = False
) -> bool:
    """
    Deletes a specified element from a given schematic after resolving its reference.
    """
    LOGGER.info(f"├── Initiating deletion sequence for target '{target_designator}' in '{schematic_name}'")

    # Delegate the search operation to the specialized module
    identified_element = find_schematic_element(app, schematic_name, target_designator, allow_partial_match)

    if identified_element is None:
        LOGGER.warning(f"└── Deletion aborted: Target element reference could not be resolved.")
        return False

    element_name = identified_element.Name

    # Execute Deletion
    try:
        delete_success = identified_element.Delete()

        if delete_success:
            LOGGER.info(f"└── Successfully DELETED element '{element_name}'.")
            return True
        else:
            LOGGER.error(f"└── API returned False while attempting to delete '{element_name}'.")
            return False

    except Exception as e:
        LOGGER.error(f"└── Encountered an exception during the deletion of '{element_name}': {e}")
        return False


# Standalone Test Execution Block
if __name__ == "__main__":
    LOGGER.info("Starting standalone test sequence for delete_element.py module.")

    try:
        test_app = mwoffice.CMWOffice()
        LOGGER.info("├── Successfully connected to AWR Microwave Office for testing.")

        result = delete_schematic_element(test_app, "Load_Pull_Template", "CFH1")

        if result:
            LOGGER.info("└── Test execution sequence completed successfully.")
        else:
            LOGGER.warning("└── Test execution completed without successful deletion.")

    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed. Details: {ex}")
        sys.exit(1)