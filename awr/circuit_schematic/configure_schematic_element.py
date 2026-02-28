"""
configure_schematic_element.py
Provides functionality to configure specific parameters of a target element.
Delegates the search logic to the isolated find_element module to comply with SRP.
Strictly adheres to the tree-branch logging hierarchy.
"""

import pyawr.mwoffice as mwoffice
import sys
from typing import Dict, Any

# Import the logger according to the established architecture
from logger.logger import LOGGER

from awr.circuit_schematic.find_element import find_schematic_element


def configure_schematic_element(
        app: Any,
        schematic_name: str,
        target_designator: str,
        parameter_map: Dict[str, Any],
        allow_partial_match: bool = False
) -> bool:
    """
    Configures specific parameters of a target element within an AWR schematic.

    Args:
        app: The active AWR MWOffice COM application instance.
        schematic_name (str): The name of the schematic in the project.
        target_designator (str): The Name or ID of the element to configure.
        parameter_map (Dict[str, Any]): A dictionary mapping parameter names to new values.
        allow_partial_match (bool): If True, allows substring matching for the element identifier.

    Returns:
        bool: True if at least one parameter was successfully updated, False otherwise.
    """
    LOGGER.info(f"├── Initiating configuration sequence for '{target_designator}' in '{schematic_name}'")

    # Delegate the search operation to the specialized module
    identified_element = find_schematic_element(app, schematic_name, target_designator, allow_partial_match)

    if identified_element is None:
        LOGGER.warning(f"└── Configuration aborted: Target element reference could not be resolved.")
        return False

    element_name = identified_element.Name
    param_items = list(parameter_map.items())
    total_params = len(param_items)
    updates_made = 0

    LOGGER.debug(f"├── Applying parameters to '{element_name}'...")

    for index, (param_key, param_value) in enumerate(param_items):
        is_last_item = (index == total_params - 1)
        tree_char = "└──" if is_last_item else "├──"

        if identified_element.Parameters.Exists(param_key):
            target_parameter = identified_element.Parameters(param_key)
            old_value = target_parameter.ValueAsString

            try:
                # Update the parameter value in the schematic
                target_parameter.ValueAsString = str(param_value)
                LOGGER.info(f"│   {tree_char} {param_key}: [{old_value}] -> [{param_value}]")
                updates_made += 1
            except Exception as e:
                LOGGER.error(f"│   {tree_char} Failed to update '{param_key}'. Exception: {e}")
        else:
            LOGGER.warning(f"│   {tree_char} Parameter '{param_key}' is missing on element '{element_name}'.")

    if updates_made > 0:
        LOGGER.info(f"└── Successfully configured {updates_made} parameter(s) for '{element_name}'.")
        return True
    else:
        LOGGER.warning(f"└── No parameters were updated for '{element_name}'.")
        return False


# Standalone Test Execution Block
if __name__ == "__main__":
    LOGGER.info("Starting standalone test sequence for configure_schematic_element.py module.")

    try:
        # Attempt to establish a connection with an active AWR instance
        test_app = mwoffice.CMWOffice()
        LOGGER.info("├── Successfully connected to AWR Microwave Office for testing.")

        # Test Parameters
        test_schematic = "Load_Pull_Template"
        test_target = "R1"
        test_params = {"R": "50", "T": "290"}

        # Execute the function
        result = configure_schematic_element(
            app=test_app,
            schematic_name=test_schematic,
            target_designator=test_target,
            parameter_map=test_params,
            allow_partial_match=False
        )

        if result:
            LOGGER.info("└── Test execution sequence completed successfully.")
        else:
            LOGGER.warning("└── Test execution completed, but the element could not be configured.")

    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed. Ensure AWR application is running. Details: {ex}")
        sys.exit(1)