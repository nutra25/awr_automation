"""
marker.py
Encapsulates all operations related to markers within AWR graphs.
Handles marker creation, movement, and value extraction.
Strictly adheres to the tree-branch logging hierarchy.
"""

import sys
from typing import Any, Optional
import pyawr.mwoffice as mwoffice
from core.logger import LOGGER
from awr.graph.perform_simulation import perform_simulation as run_sim

# Measurement class dependency for measurement toggling functionalities
from awr.graph.measurement import Measurement


class Marker:
    """
    Service class managing graph marker operations.
    """

    def __init__(self, app: Any):
        """
        Initializes the Marker operations class.

        Args:
            app (Any): The active AWR MWOffice COM application instance.
        """
        self.app = app
        self.measurement_service = Measurement(app)

    def add_and_move_marker(
            self,
            graph_name: str,
            measurement_name: str,
            marker_name: str,
            action: str = "MIN",
            search_val: Optional[float] = None,
            perform_simulation: bool = False
    ) -> None:
        """
        Attaches a marker to the graph and relocates it based on the specified action.
        """
        LOGGER.info(f"├── Initiating marker attachment and relocation sequence for graph: '{graph_name}'")

        try:
            project = self.app.Project

            if perform_simulation:
                run_sim(self.app)
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

    def move_marker(
            self,
            graph_name: str,
            marker_name: str,
            action: str = "MIN",
            search_val: Optional[float] = None,
            perform_simulation: bool = False
    ) -> bool:
        """
        Locates an existing marker on a specified graph and relocates it.
        """
        LOGGER.info(f"├── Initiating marker relocation sequence for graph: '{graph_name}', marker: '{marker_name}'")

        try:
            project = self.app.Project

            if perform_simulation:
                run_sim(self.app)
            else:
                LOGGER.debug("│   ├── Simulation skipped (perform_simulation=False).")

            if not project.Graphs.Exists(graph_name):
                LOGGER.error(f"└── Sequence aborted: Target graph '{graph_name}' does not exist.")
                return False

            graph = project.Graphs(graph_name)

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

    def get_marker_value(
            self,
            graph_title: str,
            marker_designator: str,
            perform_simulation: bool = True,
            toggle_enable: bool = False
    ) -> str:
        """
        Retrieves the data value from a specific marker on a graph in AWR Microwave Office.
        """
        LOGGER.info(f"├── Retrieving Marker Data: '{marker_designator}' from '{graph_title}'")

        try:
            project_reference = self.app.Project
            LOGGER.debug("│   ├── Connected to active project.")

            target_graph = None
            for graph in project_reference.Graphs:
                if graph.Name == graph_title:
                    target_graph = graph
                    break

            if target_graph is None:
                LOGGER.error(f"│   └── Graph NOT found: '{graph_title}'")
                raise RuntimeError(f"Graph '{graph_title}' not found.")

            LOGGER.debug(f"│   ├── Graph located: {target_graph.Name}")

            if toggle_enable:
                self.measurement_service.toggle_graph_measurements(target_graph, enable=True)

            if perform_simulation:
                run_sim(self.app)
            else:
                LOGGER.debug("│   ├── Simulation skipped (perform_simulation=False).")

            target_marker = None
            target_designator_clean = marker_designator.strip().lower()

            for marker in target_graph.Markers:
                if marker.Name.strip().lower() == target_designator_clean:
                    target_marker = marker
                    break

            if target_marker is None:
                LOGGER.error(f"│   └── Marker '{marker_designator}' NOT found on graph.")
                raise RuntimeError(f"Marker '{marker_designator}' missing.")

            raw_text = target_marker.DataValueText

            if toggle_enable:
                self.measurement_service.toggle_graph_measurements(target_graph, enable=False)

            if raw_text:
                LOGGER.info(f"│   └── Value: {raw_text}")
            else:
                LOGGER.warning("│   └── Marker value is empty.")

            return str(raw_text) if raw_text is not None else ""

        except Exception as read_error:
            LOGGER.error(f"│   └── Error reading marker data: {read_error}")
            raise RuntimeError(f"Failed to read data: {read_error}")


if __name__ == "__main__":
    LOGGER.info("├── Starting standalone test sequence for marker.py")
    try:
        test_app = mwoffice.CMWOffice()
        marker_service = Marker(test_app)

        target_graph_name = "Results"
        target_measurement_name = "PAE"
        target_marker_name = "minPAE"

        LOGGER.info(f"│   ├── Testing marker sequence on graph: '{target_graph_name}'")
        marker_service.add_and_move_marker(
            graph_name=target_graph_name,
            measurement_name=target_measurement_name,
            marker_name=target_marker_name,
            action="MIN",
            perform_simulation=False
        )

        val = marker_service.get_marker_value(target_graph_name, target_marker_name, perform_simulation=False)
        LOGGER.info(f"│   ├── Extracted Marker Value: {val}")

        LOGGER.info("└── Test execution sequence completed successfully.")
    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed: {ex}")
        sys.exit(1)