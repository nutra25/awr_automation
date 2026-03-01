"""
add_and_move_marker.py
Provides functionality to attach a marker to a specific graph measurement
and subsequently relocate it using MoveToMinimum, MoveToMaximum, or Search operations.
Strictly adheres to the tree-branch logging hierarchy and error handling protocols.
"""

import sys
from typing import Any, Optional
import pyawr.mwoffice as mwoffice
from logger.logger import LOGGER
from awr.graph.perform_simulation import perform_simulation as run_sim


def add_and_move_marker(
        app: Any,
        graph_name: str,
        measurement_name: str,
        marker_name: str,
        action: str = "MIN",
        search_val: Optional[float] = None,
        perform_simulation: bool = False
) -> None:
    """
    Attaches a marker to the graph and relocates it based on the specified action.

    Actions: "MIN", "MAX", or "SEARCH"
    If "SEARCH" is selected, the search_val parameter must be provided.

    Args:
        app (Any): The active AWR MWOffice COM application instance.
        graph_name (str): The target graph name.
        measurement_name (str): The partial or full name of the measurement to attach the marker to.
        marker_name (str): The designation for the newly created marker.
        action (str, optional): The relocation action ("MIN", "MAX", "SEARCH"). Defaults to "MIN".
        search_val (float, optional): The target Y-axis value for the "SEARCH" action. Defaults to None.
        perform_simulation (bool, optional): Indicates whether to run the simulation before operations. Defaults to False.
    """
    LOGGER.info(f"├── Initiating marker attachment and relocation sequence for graph: '{graph_name}'")

    try:
        project = app.Project

        if perform_simulation:
            run_sim(app)
        else:
            LOGGER.debug("│   ├── Simulation skipped (perform_simulation=False).")

        if not project.Graphs.Exists(graph_name):
            LOGGER.error(f"└── Sequence aborted: Target graph '{graph_name}' does not exist.")
            return

        graph = project.Graphs(graph_name)

        meas_index = -1
        target_meas = None
        for i in range(1, graph.Measurements.Count + 1):
            meas = graph.Measurements.Item(i)
            if measurement_name in meas.Name:
                meas_index = i
                target_meas = meas
                LOGGER.debug(f"│   ├── Partial match identified for measurement: '{meas.Name}'")
                break

        if meas_index == -1 or target_meas is None:
            LOGGER.error(f"└── Sequence aborted: Measurement containing '{measurement_name}' could not be located.")
            return

        if target_meas.XPointCount < 1:
            LOGGER.error("└── Sequence aborted: The target measurement contains no data points.")
            return

        first_x_val = target_meas.XValue(1)

        marker = graph.Markers.Add(meas_index, 1, first_x_val)

        if marker._get_inner() is None:
            LOGGER.error("└── Sequence aborted: Failed to instantiate the marker COM object.")
            return

        marker.Name = marker_name
        action = action.upper()

        if action == "MAX":
            success = marker.MoveToMaximum()
            LOGGER.info(f"│   ├── Marker '{marker_name}' relocated to MAX point. (Operation Success: {success})")

        elif action == "MIN":
            success = marker.MoveToMinimum()
            LOGGER.info(f"│   ├── Marker '{marker_name}' relocated to MIN point. (Operation Success: {success})")

        elif action == "SEARCH" and search_val is not None:
            search_mode = mwoffice.mwMarkerSearchMode.mwMST_Absolute
            search_dir = mwoffice.mwMarkerSearchDirection.mwMSD_SearchRight
            search_var = mwoffice.mwMarkerSearchVariable.mwMSV_Y

            success = marker.Search(search_val, search_mode, search_dir, search_var)

            if success:
                LOGGER.info(f"│   ├── Marker '{marker_name}' successfully relocated to Y={search_val}.")
            else:
                LOGGER.warning(f"│   ├── Target value {search_val} could not be found on the measurement trace.")

        else:
            LOGGER.error("└── Sequence aborted: Invalid action specified. Permitted actions: 'MIN', 'MAX', 'SEARCH'.")
            return

        LOGGER.info("└── Marker attachment and relocation sequence completed successfully.")

    except Exception as e:
        LOGGER.error(f"└── Unexpected error occurred during marker operations: {e}")


if __name__ == "__main__":
    LOGGER.info("├── Starting standalone test sequence for add_and_move_marker.py")
    try:
        test_app = mwoffice.CMWOffice()

        target_graph_name = "Results"
        target_measurement_name = "PAE"
        target_marker_name = "minPAE"

        LOGGER.info(f"│   ├── Target graph defined explicitly as: '{target_graph_name}'")
        LOGGER.info(f"│   ├── Target measurement defined explicitly as: '{target_measurement_name}'")

        add_and_move_marker(
            app=test_app,
            graph_name=target_graph_name,
            measurement_name=target_measurement_name,
            marker_name=target_marker_name,
            action="MIN",
            perform_simulation=False
        )

        LOGGER.info("└── Test execution sequence completed successfully.")
    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed: {ex}")
        sys.exit(1)