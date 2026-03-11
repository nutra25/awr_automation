import math
from typing import Any, Dict, List, Optional

from awr.awr_component import AWRComponent


class Measurement(AWRComponent):

    def add_measurement_to_graph(self, graph_name: str, source_name: str, measurement_expression: str) -> bool:

        self.logger.info(f"├── Attempting to add measurement '{measurement_expression}' from '{source_name}' to graph '{graph_name}'")

        try:
            graph = self.app.Project.Graphs.Item(graph_name)
            measurements = graph.Measurements
            measurements.Add(source_name, measurement_expression)

            self.logger.info(f"└── Successfully added measurement to graph: '{graph_name}'")
            return True

        except Exception as e:
            self.logger.error(f"└── Failed to add measurement to graph '{graph_name}'. Exception details: {e}")
            return False

    def find_measurement(self):
        """
        Placeholder for future functionality to locate specific measurements.
        """
        self.logger.debug("│   ├── find_measurement method is reserved for future implementation.")
        pass

    def extract_contours(self, graph_name: str) -> Dict[float, List[Dict[str, Any]]]:

        self.logger.info(f"Starting Data Extraction Sequence for Graph: {graph_name}")

        try:
            project = self.app.Project

            if not project.Graphs.Exists(graph_name):
                self.logger.critical(f"  └─ Graph NOT found in AWR system: {graph_name}")
                return {}

            self.logger.debug("  ├─ Graph located Instantiating data structures")

            graph = project.Graphs(graph_name)
            data_by_freq = {}

            try:

                self.logger.debug("  ├── Starting Simulation (Analyze)...")
                simulator = project.Simulator
                simulator.Analyze()
                self.logger.debug("  ├── Simulation Completed.")
            except Exception as sim_error:
                self.logger.critical(f"  └─ Simulation FAILED: {sim_error}")
                raise RuntimeError(f"Simulation execution failed: {sim_error}")

            meas_items = list(graph.Measurements)
            total_meas = len(meas_items)

            self.logger.info("  ├── Extracting Measurement Traces:")

            for m_idx, meas in enumerate(meas_items):
                is_last_meas = (m_idx == total_meas - 1)
                tree_char_m = "└──" if is_last_meas else "├──"

                if not meas.Enabled:
                    self.logger.debug(f"  │   {tree_char_m} Measurement {meas.Name}: SKIPPED (Disabled)")
                    continue

                for i in range(1, meas.TraceCount + 1):
                    try:
                        sweep_labels = meas.SweepLabels(i)
                        pae_val, freq_val = None, None

                        if sweep_labels.Count > 0:
                            for label_idx in range(1, sweep_labels.Count + 1):
                                lbl = sweep_labels.Item(label_idx)
                                name_up = lbl.Name.upper()
                                if name_up == "PAE":
                                    pae_val = float(lbl.Value)
                                elif name_up in ["F1", "FREQ", "FREQUENCY"]:
                                    freq_val = float(lbl.Value)

                        if pae_val is not None and freq_val is None:
                            freq_val = 0.0

                        if pae_val is None:
                            continue

                        data = meas.TraceValues(i)
                        if not data:
                            continue

                        islands = []
                        curr_r, curr_i = [], []

                        if isinstance(data[0], (int, float)):
                            step = 3 if len(data) % 3 == 0 else 2
                            points = []
                            for k in range(0, len(data) - (step - 1), step):
                                if step == 3:
                                    points.append((data[k], data[k + 1], data[k + 2]))
                                else:
                                    points.append((0.0, data[k], data[k + 1]))
                        else:
                            points = data

                        for pt in points:
                            r, im = pt[1], pt[2]
                            is_valid = not (math.isnan(r) or math.isinf(r) or math.isnan(im) or math.isinf(im))
                            if is_valid and (abs(r) > 3.0 or abs(im) > 3.0):
                                is_valid = False

                            if is_valid:
                                curr_r.append(r)
                                curr_i.append(im)
                            else:
                                if len(curr_r) > 2:
                                    if curr_r[0] != curr_r[-1] or curr_i[0] != curr_i[-1]:
                                        curr_r.append(curr_r[0])
                                        curr_i.append(curr_i[0])
                                    islands.append({'real': curr_r, 'imag': curr_i})
                                curr_r, curr_i = [], []

                        if len(curr_r) > 2:
                            if curr_r[0] != curr_r[-1] or curr_i[0] != curr_i[-1]:
                                curr_r.append(curr_r[0])
                                curr_i.append(curr_i[0])
                            islands.append({'real': curr_r, 'imag': curr_i})

                        if islands:
                            if freq_val not in data_by_freq:
                                data_by_freq[freq_val] = []
                            data_by_freq[freq_val].append({'pae': pae_val, 'islands': islands})

                    except Exception as e:
                        if i == 1:
                            self.logger.error(f"  │   {tree_char_m} Trace #{i} read FAILED -> {e}")

            self.logger.info("  └── Data Extraction Process Completed Successfully")
            return data_by_freq

        except Exception as e:
            self.logger.critical(f"  └─ Critical Error in Graph Data Extraction: {e}")
            raise

    def extract_single_point_data(self, graph_name: str, measurement_name: str) -> Optional[List[Any]]:

        self.logger.info("Initiating Generic Data Extraction Sequence")
        self.logger.info(f"├── Target Graph: {graph_name}")
        self.logger.info(f"├── Target Measurement: {measurement_name}")

        try:
            project = self.app.Project

            if not project.Graphs.Exists(graph_name):
                self.logger.error(f"└── Extraction Failed: Graph '{graph_name}' does not exist in the active project.")
                return None

            self.logger.debug("├── Target graph located. Executing simulation sequence.")
            self.awr.project.perform_simulation(self.app)

            graph = project.Graphs(graph_name)

            target_meas = None
            available_measurements = []

            target_clean = measurement_name.replace(" ", "").upper()

            for meas in graph.Measurements:
                meas_name = meas.Name
                available_measurements.append(meas_name)

                actual_clean = meas_name.replace(" ", "").upper()

                if target_clean in actual_clean or actual_clean in target_clean:
                    target_meas = meas
                    break

            if not target_meas:
                self.logger.error(
                    f"└── Extraction Failed: Measurement '{measurement_name}' not found within graph '{graph_name}'.")
                self.logger.debug("    ├── Available measurements in this graph according to AWR COM:")

                for idx, am in enumerate(available_measurements):
                    prefix = "└──" if idx == len(available_measurements) - 1 else "├──"
                    self.logger.debug(f"    │   {prefix} '{am}'")

                return None

            if not target_meas.Enabled:
                self.logger.warning(f"└── Extraction Aborted: Measurement '{target_meas.Name}' is currently disabled.")
                return None

            self.logger.debug(f"├── Target measurement verified as: '{target_meas.Name}'. Fetching raw trace values.")

            try:
                raw_data = target_meas.TraceValues(1)

                if not raw_data:
                    self.logger.error("└── Extraction Failed: Retrieved trace data is empty.")
                    return None

                data_list = list(raw_data)

                self.logger.info(
                    f"└── Data extraction completed successfully. Retrieved {len(data_list)} primary data elements.")
                return data_list

            except Exception as e:
                self.logger.error(f"└── Trace read operation failed for measurement '{target_meas.Name}': {e}")
                return None

        except Exception as e:
            self.logger.error(f"└── Critical framework error during data extraction: {e}")
            return None