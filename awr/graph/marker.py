import re
from typing import Optional, List, Literal, Dict, Any
from pyawr import mwoffice

from awr.awr_component import AWRComponent


class Marker(AWRComponent):

    def add_marker(self, graph_name: str, measurement_name: str, marker_name: str, perform_simulation: bool = False, allow_partial_match: bool = False) -> bool:
        # TEST ET
        """
        Adds a new marker to a specific measurement on a graph at the first available data point.

        Args:
            graph_name (str): The exact name of the target graph.
            measurement_name (str): The name of the measurement to attach the marker to.
            marker_name (str): The desired name for the new marker (e.g., "m1").
            perform_simulation (bool): If True, triggers analysis before adding the marker.
            allow_partial_match (bool): If True, allows substring matching for the measurement name.

        Returns:
            bool: True if the marker was successfully added, False otherwise.
        """
        self.logger.info(f"├── Initiating marker addition sequence for graph: '{graph_name}', marker: '{marker_name}'")

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

            meas_index = -1
            target_meas = None

            if allow_partial_match:
                target_clean = measurement_name.replace(" ", "").upper()

            for i in range(1, graph.Measurements.Count + 1):
                meas = graph.Measurements.Item(i)

                if allow_partial_match:
                    actual_clean = meas.Name.replace(" ", "").upper()
                    if target_clean in actual_clean or actual_clean in target_clean:
                        meas_index = i
                        target_meas = meas
                        self.logger.debug(
                            f"│   ├── Partial match identified for measurement: '{meas.Name}' at index {i}")
                        break
                else:
                    if meas.Name == measurement_name:
                        meas_index = i
                        target_meas = meas
                        self.logger.debug(f"│   ├── Exact match identified for measurement: '{meas.Name}' at index {i}")
                        break

            if meas_index == -1 or target_meas is None:
                self.logger.error(
                    f"└── Sequence aborted: Measurement '{measurement_name}' could not be located in graph '{graph_name}'.")
                return False

            if target_meas.XPointCount < 1:
                self.logger.error(
                    "└── Sequence aborted: The target measurement contains no data points. Cannot attach marker.")
                return False

            first_x_val = target_meas.XValue(1)

            marker = graph.Markers.Add(meas_index, 1, first_x_val)

            if marker is None or marker._get_inner() is None:
                self.logger.error("└── Sequence aborted: Failed to instantiate the marker COM object.")
                return False

            marker.Name = marker_name
            self.logger.info(
                f"│   ├── Marker '{marker_name}' successfully added to '{target_meas.Name}' at X={first_x_val}.")
            self.logger.info("└── Marker addition sequence completed successfully.")

            return True

        except Exception as e:
            self.logger.error(f"└── Unexpected error occurred during marker addition: {e}")
            return False

    def move_marker(
            self,
            graph_name: str,
            marker_name: str,
            action: Literal["MIN", "MAX", "SEARCH"] = "MIN",
            search_val: Optional[float] = None,
            search_mode: Literal["mwMST_Absolute", "mwMST_Relative"] = "mwMST_Absolute",
            search_dir: Literal["mwMSD_SearchRight", "mwMSD_SearchLeft", "mwMSD_SearchUp", "mwMSD_SearchDown"] = "mwMSD_SearchRight",
            search_var: Literal["mwMSV_X", "mwMSV_Y"] = "mwMSV_Y",
            perform_simulation: bool = False
    ) -> bool:
        # TEST ET
        """
        Relocates an existing marker to a specific point on the trace.

        Args:
            graph_name (str): The exact name of the target graph.
            marker_name (str): The name of the marker to be moved (e.g., "m1").
            action (Literal["MIN", "MAX", "SEARCH"]): The movement behavior.
            search_val (Optional[float]): The target value. ONLY used when action is "SEARCH".
            search_mode: The AWR search mode (Absolute or Relative). Default is Absolute.
            search_dir: The direction to search (Right, Left, Up, Down). Default is Right.
            search_var: The variable to search against (X or Y axis). Default is Y.
            perform_simulation (bool): If True, triggers analysis before moving the marker.

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        self.logger.info(
            f"├── Initiating marker relocation sequence for graph: '{graph_name}', marker: '{marker_name}'")

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
                self.logger.error(
                    f"└── Sequence aborted: Marker '{marker_name}' could not be located on graph '{graph_name}'.")
                return False

            action = action.upper()
            operation_success = False

            if action == "MAX":
                operation_success = target_marker.MoveToMaximum()
                self.logger.info(
                    f"│   ├── Marker '{marker_name}' relocated to MAX point. (Operation Success: {operation_success})")

            elif action == "MIN":
                operation_success = target_marker.MoveToMinimum()
                self.logger.info(
                    f"│   ├── Marker '{marker_name}' relocated to MIN point. (Operation Success: {operation_success})")

            elif action == "SEARCH":
                if search_val is None:
                    self.logger.error("└── Sequence aborted: 'search_val' MUST be provided when action is 'SEARCH'.")
                    return False
                try:
                    s_mode = getattr(mwoffice.mwMarkerSearchMode, search_mode)
                    s_dir = getattr(mwoffice.mwMarkerSearchDirection, search_dir)
                    s_var = getattr(mwoffice.mwMarkerSearchVariable, search_var)
                except AttributeError as attr_err:
                    self.logger.error(f"└── Sequence aborted: Invalid search parameter passed. Details: {attr_err}")
                    return False

                operation_success = target_marker.Search(search_val, s_mode, s_dir, s_var)

                if operation_success:
                    self.logger.info(
                        f"│   ├── Marker '{marker_name}' successfully relocated to {search_var[-1]}={search_val} (Mode: {search_mode}, Dir: {search_dir}).")
                else:
                    self.logger.warning(
                        f"│   ├── Target value {search_val} could not be found on the trace for marker '{marker_name}'.")

            else:
                self.logger.error(
                    "└── Sequence aborted: Invalid action specified. Permitted actions: 'MIN', 'MAX', 'SEARCH'.")
                return False

            if operation_success:
                self.logger.info("└── Marker relocation sequence completed successfully.")
            else:
                self.logger.warning("└── Marker relocation sequence finished, but the operation reported failure.")

            return operation_success

        except Exception as e:
            self.logger.error(f"└── Unexpected error occurred during marker relocation: {e}")
            return False

    def get_marker_data(self, graph_title: str, marker_designator: str, perform_simulation: bool = False, toggle_enable: bool = False) -> Dict[str, Any]:
        """
        Retrieves marker text data and parses it into a structured dictionary mapping labels to their numeric values.
        """
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
                return {}

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
                return {}

            raw_text = target_marker.DataValueText

            if toggle_enable:
                self.awr.graph.measurement.toggle_graph_measurements(target_graph, enable=False)

            if not raw_text:
                self.logger.warning("│   └── Marker value is empty. Returning empty structured data.")
                return {'marker_name': marker_designator, 'data': {}, 'unlabeled': [], 'raw_text': ""}

            self.logger.info(f"│   ├── Raw Text Read: {str(raw_text).replace(chr(10), ' | ')}")

            parsed_data = {}
            unlabeled_values = []

            lines = re.split(r'[\n\r,]+', str(raw_text))

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                match = re.search(r'([a-zA-Z]+[a-zA-Z0-9_]*)\s*[:=]?\s*(-?\d+\.?\d*(?:[eE][-+]?\d+)?)', line)

                if match:
                    key = match.group(1).strip()
                    val = float(match.group(2))
                    parsed_data[key] = val
                else:
                    nums = re.findall(r'-?\d+\.?\d*(?:[eE][-+]?\d+)?', line)
                    for n in nums:
                        unlabeled_values.append(float(n))

            result = {
                'marker_name': marker_designator,
                'data': parsed_data,
                'unlabeled': unlabeled_values,
                'raw_text': raw_text
            }

            log_data_str = ", ".join([f"{k}={v}" for k, v in parsed_data.items()])
            self.logger.debug(f"│   └── Structured Data: [{log_data_str}] | Unlabeled: {unlabeled_values}")
            self.logger.info("└── Marker data retrieval sequence completed successfully.")

            return result

        except Exception as read_error:
            self.logger.error(f"│   └── Error reading/parsing marker data: {read_error}")
            return {}