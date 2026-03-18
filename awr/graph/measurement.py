import math
from typing import Any, Dict, List, Optional

from awr.awr_component import AWRComponent


class Measurement(AWRComponent):

    def add_measurement_to_graph(self, graph_name: str, source_name: str, measurement_expression: str) -> bool:
        # ONAYLANDI
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

    def find_measurement(self, graph_name: str, measurement_name: str, allow_partial_match: bool = False) -> Optional[Any]:
        # ONAYLANDI
        """
        Locates a specific measurement within a designated graph.
        If allow_partial_match is True, it ignores spaces, case, and accepts substring matches.
        Returns the AWR measurement COM object if found, otherwise None.
        """
        match_type = "Partial/Tolerant" if allow_partial_match else "Strict"
        self.logger.info(
            f"├── Searching for measurement '{measurement_name}' in graph '{graph_name}' (Mode: {match_type})")

        try:
            project = self.app.Project

            if not project.Graphs.Exists(graph_name):
                self.logger.error(f"└── Search Failed: Graph '{graph_name}' does not exist in the active project.")
                return None

            graph = project.Graphs(graph_name)

            if allow_partial_match:
                target_clean = measurement_name.replace(" ", "").upper()

            for meas in graph.Measurements:
                if not allow_partial_match:
                    if meas.Name == measurement_name:
                        self.logger.info(f"└── Successfully located exact measurement: '{meas.Name}'")
                        return meas
                else:
                    actual_clean = meas.Name.replace(" ", "").upper()
                    if target_clean in actual_clean or actual_clean in target_clean:
                        self.logger.info(f"└── Successfully located partial measurement match: '{meas.Name}'")
                        return meas

            self.logger.warning(f"└── Measurement '{measurement_name}' was not found in graph '{graph_name}'.")
            return None

        except Exception as e:
            self.logger.error(f"└── Critical error while searching for measurement '{measurement_name}': {e}")
            return None

    def extract_contours(self, graph_name: str, measurement_name: str, allow_partial_match: bool = False) -> List[Dict[str, Any]]:
        # ONAYLANDI
        self.logger.info(
            f"Starting Data Extraction Sequence for Graph: '{graph_name}', Measurement: '{measurement_name}'")

        try:
            target_meas = self.find_measurement(graph_name, measurement_name, allow_partial_match)

            if not target_meas:
                self.logger.error("  └─ Extraction aborted: Measurement not found.")
                return []

            if not target_meas.Enabled:
                self.logger.warning(f"  └─ Extraction Aborted: Measurement '{target_meas.Name}' is disabled.")
                return []

            all_contours = []

            self.logger.info(f"  ├── Extracting Traces for '{target_meas.Name}'...")

            for i in range(1, target_meas.TraceCount + 1):
                try:
                    sweep_labels = target_meas.SweepLabels(i)
                    constants = {}

                    if sweep_labels.Count > 0:
                        for label_idx in range(1, sweep_labels.Count + 1):
                            lbl = sweep_labels.Item(label_idx)
                            try:
                                constants[lbl.Name] = float(lbl.Value)
                            except ValueError:
                                constants[lbl.Name] = lbl.Value

                    if not constants:
                        constants = {"Info": "No constants found"}

                    data = target_meas.TraceValues(i)
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
                        contour_id = len(all_contours) + 1
                        all_contours.append({
                            'contour_id': contour_id,
                            'constants': constants,
                            'islands': islands
                        })

                except Exception as e:
                    if i == 1:
                        self.logger.error(f"  │   ├── Trace #{i} read FAILED -> {e}")

            self.logger.info(f"  ├── Found {len(all_contours)} contours in total.")
            self.logger.info("  └── Data Extraction Process Completed Successfully")
            return all_contours

        except Exception as e:
            self.logger.critical(f"  └─ Critical Error in Graph Data Extraction: {e}")
            raise

    def extract_point_data(self, graph_name: str, measurement_name: str, allow_partial_match: bool = False) -> List[Dict[str, Any]]:
        # ONAYLANDI
        self.logger.info(f"Starting Point Data Extraction for Graph: '{graph_name}', Measurement: '{measurement_name}'")

        try:
            target_meas = self.find_measurement(graph_name, measurement_name, allow_partial_match)

            if not target_meas:
                self.logger.error(f"  └─ Extraction Failed: Measurement '{measurement_name}' not found.")
                return []

            if not target_meas.Enabled:
                self.logger.warning(f"  └─ Extraction Aborted: Measurement '{target_meas.Name}' is disabled.")
                return []

            self.logger.info(f"  ├── Extracting Traces/Points for '{target_meas.Name}'...")

            all_points = []

            # Birden fazla nokta (trace) varsa hepsini döngüyle alıyoruz
            for i in range(1, target_meas.TraceCount + 1):
                try:
                    sweep_labels = target_meas.SweepLabels(i)
                    constants = {}

                    # Tıpkı kontürdeki gibi PAE, iPower, F1 gibi verileri "constants" olarak topluyoruz
                    if sweep_labels.Count > 0:
                        for label_idx in range(1, sweep_labels.Count + 1):
                            lbl = sweep_labels.Item(label_idx)
                            try:
                                constants[lbl.Name] = float(lbl.Value)
                            except ValueError:
                                constants[lbl.Name] = lbl.Value

                    if not constants:
                        constants = {"Info": "No constants found"}

                    raw_data = target_meas.TraceValues(i)
                    if not raw_data:
                        continue

                    data = list(raw_data)

                    # AWR veri formatını çözümleyip Real/Imag koordinatlarını alıyoruz
                    if isinstance(data[0], (int, float)):
                        step = 3 if len(data) % 3 == 0 else 2
                        for k in range(0, len(data) - (step - 1), step):
                            if step == 3:
                                r, im = data[k + 1], data[k + 2]
                            else:
                                r, im = data[k], data[k + 1]

                            is_valid = not (math.isnan(r) or math.isinf(r) or math.isnan(im) or math.isinf(im))

                            if is_valid:
                                # Fotoğraftaki Mag ve Ang değerlerini AWR gibi hesaplıyoruz
                                mag = math.sqrt(r ** 2 + im ** 2)
                                ang = math.degrees(math.atan2(im, r))

                                p_id = len(all_points) + 1
                                all_points.append({
                                    'point_id': p_id,
                                    'constants': constants,  # (PAE, iPower, F1 vb. burada)
                                    'real': r,
                                    'imag': im,
                                    'mag': mag,
                                    'ang': ang
                                })
                    else:
                        # Eğer data formatı farklı gelirse (Tuple listesi vb.)
                        for pt in data:
                            r, im = pt[1], pt[2]
                            is_valid = not (math.isnan(r) or math.isinf(r) or math.isnan(im) or math.isinf(im))
                            if is_valid:
                                mag = math.sqrt(r ** 2 + im ** 2)
                                ang = math.degrees(math.atan2(im, r))

                                p_id = len(all_points) + 1
                                all_points.append({
                                    'point_id': p_id,
                                    'constants': constants,
                                    'real': r,
                                    'imag': im,
                                    'mag': mag,
                                    'ang': ang
                                })

                except Exception as e:
                    if i == 1:
                        self.logger.error(f"  │   ├── Trace #{i} read FAILED -> {e}")

            # Terminal logunu şık bir şekilde bastırıyoruz
            self.logger.info(f"  ├── Found {len(all_points)} data points in total.")
            for pt in all_points:
                c_consts = ", ".join([f"{k}={v}" for k, v in pt['constants'].items()])
                # Hem hesplanan veriyi hem de okunan etiketleri logla
                self.logger.debug(
                    f"  │   ├── Point {pt['point_id']}: Mag={pt['mag']:.4f}, Ang={pt['ang']:.2f} | Constants: [{c_consts}]")

            self.logger.info("  └── Data Extraction Process Completed Successfully")
            return all_points

        except Exception as e:
            self.logger.error(f"  └─ Critical error during data extraction: {e}")
            return []