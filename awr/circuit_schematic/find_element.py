"""
find_element.py
Provides isolated functionality to locate specific elements within an AWR schematic.
Supports both exact matches (returning a single COM object) and partial matches
(returning a list of matching COM objects for bulk operations).
Strictly adheres to the tree-branch logging hierarchy.
"""

import pyawr.mwoffice as mwoffice
import sys
from typing import Optional, Any, Union, List

from logger.logger import LOGGER

def find_schematic_element(
        app: Any,
        schematic_name: str,
        target_designator: str,
        allow_partial_match: bool = False
) -> Union[Any, List[Any], None]:
    """
    Locates a specified element from a given schematic by Name or ID.

    Args:
        app: The active AWR MWOffice COM application instance.
        schematic_name (str): The exact name of the target schematic.
        target_designator (str): The name or ID of the element to be located.
        allow_partial_match (bool): If True, returns a list of ALL elements containing the substring.
                                    If False, returns ONLY the first exact match as a single object.

    Returns:
        A list of COM objects (if allow_partial_match=True),
        a single COM object (if allow_partial_match=False and found),
        an empty list (if partial match finds nothing),
        or None (if exact match finds nothing).
    """
    LOGGER.info(f"├── Initiating element search sequence: Schematic='{schematic_name}', Target='{target_designator}'")
    LOGGER.debug(f"│   ├── Mode: {'Partial Match (Bulk)' if allow_partial_match else 'Exact Match (Single)'}")

    try:
        active_schematic = app.Project.Schematics(schematic_name)
    except Exception:
        LOGGER.error(f"└── Failed to locate schematic: '{schematic_name}'. Search sequence aborted.")
        return [] if allow_partial_match else None

    matched_elements = []

    for candidate_element in active_schematic.Elements:
        element_identifier = candidate_element.Name
        is_match = False

        # Name Matching Logic
        if allow_partial_match:
            if target_designator in element_identifier:
                is_match = True
        else:
            if target_designator == element_identifier:
                is_match = True

        # ID Matching Logic (Fallback)
        if not is_match and candidate_element.Parameters.Exists("ID"):
            element_id_value = candidate_element.Parameters("ID").ValueAsString
            if allow_partial_match:
                if target_designator in element_id_value:
                    is_match = True
            else:
                if element_id_value == target_designator:
                    is_match = True

        # Handle Match Processing
        if is_match:
            if not allow_partial_match:
                LOGGER.debug(f"│   ├── Exact target element identified: {candidate_element.Name}")
                LOGGER.info(f"└── Search sequence completed successfully.")
                return candidate_element  # Return immediately for exact match
            else:
                matched_elements.append(candidate_element)

    # Finalization for Partial Matches
    if allow_partial_match:
        if matched_elements:
            LOGGER.info(f"└── Search sequence completed. Found {len(matched_elements)} matching element(s).")
            return matched_elements
        else:
            LOGGER.warning(f"└── No elements found containing the substring '{target_designator}'.")
            return []

    # Finalization for Exact Match (Not Found scenario)
    LOGGER.warning(f"└── Exact element '{target_designator}' could not be found in '{schematic_name}'.")
    return None


# Standalone Test Execution Block
if __name__ == "__main__":
    LOGGER.info("Starting standalone test sequence for find_element.py module.")

    try:
        test_app = mwoffice.CMWOffice()
        LOGGER.info("├── Successfully connected to AWR Microwave Office for testing.")

        test_schematic = "Load_Pull_Template"

        # Test Case 1: Exact Match
        LOGGER.info("├── Test Case 1: Exact Match Mode")
        exact_target = "CFH1"
        exact_result = find_schematic_element(test_app, test_schematic, exact_target, allow_partial_match=False)
        if exact_result and not isinstance(exact_result, list):
            LOGGER.info(f"│   └── Test 1 Passed. Element resolved: {exact_result.Name}")
        else:
            LOGGER.warning("│   └── Test 1 Failed or Element not found.")

        # Test Case 2: Partial Match (Bulk)
        partial_target = "PORT"
        LOGGER.info(f"├── Test Case 2: Partial Match Mode (e.g., finding all Resistors '{partial_target}')")
        partial_results = find_schematic_element(test_app, test_schematic, partial_target, allow_partial_match=True)

        if isinstance(partial_results, list):
            LOGGER.info(f"│   └── Test 2 Passed. Retrieved a list of {len(partial_results)} element(s).")
            for el in partial_results:
                LOGGER.debug(f"│       ├── Match: {el.Name}")
        else:
            LOGGER.warning("│   └── Test 2 Failed. Did not return a list.")

        LOGGER.info("└── Test execution sequence finalized.")

    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed. Details: {ex}")
        sys.exit(1)