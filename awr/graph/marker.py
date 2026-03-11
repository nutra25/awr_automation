import re
from typing import Optional, List

from pyawr import mwoffice

from awr.awr_component import AWRComponent


class Marker(AWRComponent):

    def add_and_move_marker(self,graph_name: str,measurement_name: str,marker_name: str,action: str = "MIN",search_val: Optional[float] = None,perform_simulation: bool = False) -> None:
        self.logger.info(f"├── Initiating marker attachment and relocation sequence for graph: '{graph_name}'")

        try:
            project = self.app.Project

            if perform_simulation:
                self.awr.project.perform_simulation(self.app)
            else:
                self.logger.debug("│   ├── Simulation skipped (perform_simulation=False).")

            if not project.Graphs.Exists(graph_name):
                self.logger.error(f"└── Sequence aborted: Target graph '{graph_name}' does not exist.")
                return

            graph = project.Graphs(graph_name)

            meas_index = -1
            target_meas = None
            for i in range(1, graph.Measurements.Count + 1):
                meas = graph.Measurements.Item(i)
                if measurement_name in meas.Name:
                    meas_index = i
                    target_meas = meas
                    self.logger.debug(f"│   ├── Partial match identified for measurement: '{meas.Name}'")
                    break

            if meas_index == -1 or target_meas is None:
                self.logger.error(f"└── Sequence aborted: Measurement containing '{measurement_name}' could not be located.")
                return

            if target_meas.XPointCount < 1:
                self.logger.error("└── Sequence aborted: The target measurement contains no data points.")
                return

            first_x_val = target_meas.XValue(1)

            marker = graph.Markers.Add(meas_index, 1, first_x_val)

            if marker._get_inner() is None:
                self.logger.error("└── Sequence aborted: Failed to instantiate the marker COM object.")
                return

            marker.Name = marker_name
            action = action.upper()

            if action == "MAX":
                success = marker.MoveToMaximum()
                self.logger.info(f"│   ├── Marker '{marker_name}' relocated to MAX point. (Operation Success: {success})")

            elif action == "MIN":
                success = marker.MoveToMinimum()
                self.logger.info(f"│   ├── Marker '{marker_name}' relocated to MIN point. (Operation Success: {success})")

            elif action == "SEARCH" and search_val is not None:
                search_mode = mwoffice.mwMarkerSearchMode.mwMST_Absolute
                search_dir = mwoffice.mwMarkerSearchDirection.mwMSD_SearchRight
                search_var = mwoffice.mwMarkerSearchVariable.mwMSV_Y

                success = marker.Search(search_val, search_mode, search_dir, search_var)

                if success:
                    self.logger.info(f"│   ├── Marker '{marker_name}' successfully relocated to Y={search_val}.")
                else:
                    self.logger.warning(f"│   ├── Target value {search_val} could not be found on the measurement trace.")

            else:
                self.logger.error("└── Sequence aborted: Invalid action specified. Permitted actions: 'MIN', 'MAX', 'SEARCH'.")
                return

            self.logger.info("└── Marker attachment and relocation sequence completed successfully.")

        except Exception as e:
            self.logger.error(f"└── Unexpected error occurred during marker operations: {e}")

    def move_marker(
            self,
            graph_name: str,
            marker_name: str,
            action: str = "MIN",
            search_val: Optional[float] = None,
            perform_simulation: bool = False
    ) -> bool:

        self.logger.info(f"├── Initiating marker relocation sequence for graph: '{graph_name}', marker: '{marker_name}'")

        try:
            project = self.app.Project

            if perform_simulation:
                self.awr.project.perform_simulation(self.app)
            else:
                self.logger.debug("│   ├── Simulation skipped (perform_simulation=False).")

            if not project.Graphs.Exists(graph_name):
                self.logger.error(f"└── Sequence aborted: Target graph '{graph_name}' does not exist.")
                return False

            graph = project.Graphs(graph_name)

            target_marker = None
            for i in range(1, graph.Markers.Count + 1):
                current_marker = graph.Markers.Item(i)
                if current_marker.Name == marker_name:
                    target_marker = current_marker
                    self.logger.debug(f"│   ├── Marker '{marker_name}' identified successfully.")
                    break

            if target_marker is None:
                self.logger.error(f"└── Sequence aborted: Marker '{marker_name}' could not be located on graph '{graph_name}'.")
                return False

            action = action.upper()
            operation_success = False

            if action == "MAX":
                operation_success = target_marker.MoveToMaximum()
                self.logger.info(f"│   ├── Marker '{marker_name}' relocated to MAX point. (Operation Success: {operation_success})")

            elif action == "MIN":
                operation_success = target_marker.MoveToMinimum()
                self.logger.info(f"│   ├── Marker '{marker_name}' relocated to MIN point. (Operation Success: {operation_success})")

            elif action == "SEARCH" and search_val is not None:
                search_mode = mwoffice.mwMarkerSearchMode.mwMST_Absolute
                search_dir = mwoffice.mwMarkerSearchDirection.mwMSD_SearchRight
                search_var = mwoffice.mwMarkerSearchVariable.mwMSV_Y

                operation_success = target_marker.Search(search_val, search_mode, search_dir, search_var)

                if operation_success:
                    self.logger.info(f"│   ├── Marker '{marker_name}' successfully relocated to Y={search_val}.")
                else:
                    self.logger.warning(f"│   ├── Target value {search_val} could not be found on the trace for marker '{marker_name}'.")

            else:
                self.logger.error("└── Sequence aborted: Invalid action specified. Permitted actions: 'MIN', 'MAX', 'SEARCH'.")
                return False

            if operation_success:
                self.logger.info("└── Marker relocation sequence completed successfully.")
            else:
                self.logger.warning("└── Marker relocation sequence finished, but the operation reported failure.")

            return operation_success

        except Exception as e:
            self.logger.error(f"└── Unexpected error occurred during marker relocation: {e}")
            return False

    def get_marker_data(self, graph_title: str, marker_designator: str, perform_simulation: bool = True, toggle_enable: bool = False ) -> List[float]:

        self.logger.info(f"├── Retrieving Marker Data: '{marker_designator}' from '{graph_title}'")

        try:
            project_reference = self.app.Project
            self.logger.debug("│   ├── Connected to active project.")

            target_graph = None
            for graph in project_reference.Graphs:
                if graph.Name == graph_title:
                    target_graph = graph
                    break

            if target_graph is None:
                self.logger.error(f"│   └── Graph NOT found: '{graph_title}'")
                raise RuntimeError(f"Graph '{graph_title}' not found.")

            self.logger.debug(f"│   ├── Graph located: {target_graph.Name}")

            if toggle_enable:
                self.awr.graph.measurement.toggle_graph_measurements(target_graph, enable=True)

            if perform_simulation:
                self.awr.project.perform_simulation(self.app)
            else:
                self.logger.debug("│   ├── Simulation skipped (perform_simulation=False).")

            target_marker = None
            target_designator_clean = marker_designator.strip().lower()

            for marker in target_graph.Markers:
                if marker.Name.strip().lower() == target_designator_clean:
                    target_marker = marker
                    break

            if target_marker is None:
                self.logger.error(f"│   └── Marker '{marker_designator}' NOT found on graph.")
                raise RuntimeError(f"Marker '{marker_designator}' missing.")

            raw_text = target_marker.DataValueText

            if toggle_enable:
                self.awr.graph.measurement.toggle_graph_measurements(target_graph, enable=False)

            if not raw_text:
                self.logger.warning("│   └── Marker value is empty. Returning default [0.0, 0.0, 0.0].")
                return [0.0, 0.0, 0.0]

            self.logger.info(f"│   └── Raw Value: {raw_text}")

            numbers = re.findall(r"-?\d+\.?\d*", str(raw_text))

            parsed_data = [float(n) for n in numbers]

            self.logger.debug(f"│   └── Parsed Data: {parsed_data}")
            return parsed_data

        except Exception as read_error:
            self.logger.error(f"│   └── Error reading/parsing marker data: {read_error}")
            raise RuntimeError(f"Failed to read data: {read_error}")