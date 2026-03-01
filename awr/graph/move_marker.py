"""
move_marker.py
Provides functionality to locate an existing marker on a specific graph
and relocate it using MoveToMinimum, MoveToMaximum, or Search operations.
Strictly adheres to the tree-branch logging hierarchy and error handling protocols.
"""

import sys
from typing import Any, Optional
import pyawr.mwoffice as mwoffice
from logger.logger import LOGGER
from awr.graph.perform_simulation import perform_simulation as run_sim


def move_marker(
        app: Any,
        graph_name: str,
        marker_name: str,
        action: str = "MIN",
        search_val: Optional[float] = None,
        perform_simulation: bool = False
) -> bool:
    """
    Locates an existing marker on a specified graph and relocates it.

    Actions: "MIN", "MAX", or "SEARCH"
    If "SEARCH" is selected, the search_val parameter must be provided.

    Args:
        app (Any): The active AWR MWOffice COM application instance.
        graph_name (str): The target graph name where the marker resides.
        marker_name (str): The exact name of the marker to be relocated.
        action (str, optional): The relocation action ("MIN", "MAX", "SEARCH"). Defaults to "MIN".
        search_val (float, optional): The target Y-axis value for the "SEARCH" action. Defaults to None.
        perform_simulation (bool, optional): Indicates whether to run the simulation before operations. Defaults to False.

    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    LOGGER.info(f"├── Initiating marker relocation sequence for graph: '{graph_name}', marker: '{marker_name}'")

    try:
        project = app.Project

        # Execute simulation if requested
        if perform_simulation:
            run_sim(app)
        else:
            LOGGER.debug("│   ├── Simulation skipped (perform_simulation=False).")

        # Validate graph existence
        if not project.Graphs.Exists(graph_name):
            LOGGER.error(f"└── Sequence aborted: Target graph '{graph_name}' does not exist.")
            return False

        graph = project.Graphs(graph_name)

        # Locate the specific marker by its exact name
        target_marker = None
        for i in range(1, graph.Markers.Count + 1):
            current_marker = graph.Markers.Item(i)
            if current_marker.Name == marker_name:
                target_marker = current_marker
                LOGGER.debug(f"│   ├── Marker '{marker_name}' identified successfully.")
                break

        if target_marker is None:
            LOGGER.error(f"└── Sequence aborted: Marker '{marker_name}' could not be located on graph '{graph_name}'.")
            return False

        action = action.upper()
        operation_success = False

        # Execute the specified relocation sequence
        if action == "MAX":
            operation_success = target_marker.MoveToMaximum()
            LOGGER.info(f"│   ├── Marker '{marker_name}' relocated to MAX point. (Operation Success: {operation_success})")

        elif action == "MIN":
            operation_success = target_marker.MoveToMinimum()
            LOGGER.info(f"│   ├── Marker '{marker_name}' relocated to MIN point. (Operation Success: {operation_success})")

        elif action == "SEARCH" and search_val is not None:
            search_mode = mwoffice.mwMarkerSearchMode.mwMST_Absolute
            search_dir = mwoffice.mwMarkerSearchDirection.mwMSD_SearchRight
            search_var = mwoffice.mwMarkerSearchVariable.mwMSV_Y

            operation_success = target_marker.Search(search_val, search_mode, search_dir, search_var)

            if operation_success:
                LOGGER.info(f"│   ├── Marker '{marker_name}' successfully relocated to Y={search_val}.")
            else:
                LOGGER.warning(f"│   ├── Target value {search_val} could not be found on the trace for marker '{marker_name}'.")

        else:
            LOGGER.error("└── Sequence aborted: Invalid action specified. Permitted actions: 'MIN', 'MAX', 'SEARCH'.")
            return False

        if operation_success:
            LOGGER.info("└── Marker relocation sequence completed successfully.")
        else:
            LOGGER.warning("└── Marker relocation sequence finished, but the operation reported failure.")

        return operation_success

    except Exception as e:
        LOGGER.error(f"└── Unexpected error occurred during marker relocation: {e}")
        return False


if __name__ == "__main__":
    LOGGER.info("├── Starting standalone test sequence for move_marker.py")
    try:
        test_app = mwoffice.CMWOffice()

        # Hardcoded parameters for isolated testing
        target_graph_name = "Results"
        target_marker_name = "minPAE"

        LOGGER.info(f"│   ├── Target graph defined explicitly as: '{target_graph_name}'")
        LOGGER.info(f"│   ├── Target marker defined explicitly as: '{target_marker_name}'")

        # Execute MoveToMinimum sequence
        move_marker(
            app=test_app,
            graph_name=target_graph_name,
            marker_name=target_marker_name,
            action="MIN",
            perform_simulation=False
        )

        LOGGER.info("└── Test execution sequence completed successfully.")
    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed: {ex}")
        sys.exit(1)