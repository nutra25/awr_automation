from config import *
from logger import LOGGER
import itertools
import csv
import re
from typing import List, Tuple, Any, Dict
from enum import Enum, auto
import objects

# API Functions
from pyawr_get_marker_value import get_marker_value
from pyawr_configure_schematic_element import configure_schematic_element
from pyawr_loadpull_wizard import run_loadpull_wizard
from pyawr_configure_schematic_rf_frequency import configure_schematic_rf_frequency

logger = LOGGER


class PullType(Enum):
    LOADPULL = auto()
    SOURCEPULL = auto()


class AWRDriver:
    """Interface for AWR Microwave Office API operations."""

    @staticmethod
    def configure_element(element_name: str, params: dict):
        configure_schematic_element(
            schematic_title=SCHEMATIC_NAME,
            target_designator=element_name,
            parameter_map=params,
        )
        logger.debug(f"Configured {element_name}: {params}")

    @staticmethod
    def set_frequency(freq: float):
        configure_schematic_rf_frequency(
            schematic_name=SCHEMATIC_NAME,
            frequencies=freq
        )

    @staticmethod
    def get_marker_data(graph: str, marker: str, toggle_enable: bool = False) -> List[float]:
        raw_output = get_marker_value(
            graph_title=graph,
            marker_designator=marker,
            perform_simulation=True,
            toggle_enable=toggle_enable
        )

        if not raw_output:
            logger.warning(f"No data from {marker} on {graph}")
            return [0.0, 0.0, 0.0]

        numbers = re.findall(r"-?\d+\.?\d*", raw_output)
        return [float(n) for n in numbers]

    @staticmethod
    def run_wizard(options: dict):
        run_loadpull_wizard(options)


class ResultsLogger:
    """Handles CSV initialization and data persistence."""

    def __init__(self, filename=FILENAME):
        self.filename = filename
        self.headers = self._generate_headers()
        self._init_file()

    def _generate_headers(self) -> List[str]:
        state_headers = [var.name for var in STATE_VAR]
        measure_headers = [m["header"] for m in MEASUREMENT_CONFIG]
        tuner_headers = ["Best_Source_Mag", "Best_Source_Ang", "Best_Load_Mag", "Best_Load_Ang"]

        iteration_headers = []
        for i in range(ITERATION_COUNT):
            for mode in ["SP", "LP"]:
                iteration_headers.extend([f"{mode}_It{i + 1}_Point", f"{mode}_It{i + 1}_Mag", f"{mode}_It{i + 1}_Ang"])

        return state_headers + measure_headers + tuner_headers + iteration_headers

    def _init_file(self):
        try:
            with open(self.filename, mode='w', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow(self.headers)
            logger.info(f"Initialized output: {self.filename}")
        except IOError as e:
            logger.error(f"IO Error: {e}")
            raise

    def log_state(self, state_values: Tuple, results: List[Any], measured_data: dict, best_tuner_data: Tuple):
        measured_row = [measured_data[m["header"]] for m in MEASUREMENT_CONFIG]
        row = list(state_values) + measured_row + list(best_tuner_data)

        for res in results:
            row.extend([res.point, res.mag, res.ang])

        with open(self.filename, mode='a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(row)
            f.flush()


class SimulationManager:
    """Orchestrates the multi-iteration load-pull simulation process."""
    _PULL_CONFIG = {
        PullType.SOURCEPULL: {
            "active_side": "SOURCE",  # Tuner Settings key
            "fixed_side": "LOAD",
            "mode_str": "SP",
            "file_prefix": "source",
            "opposite": PullType.LOADPULL
        },
        PullType.LOADPULL: {
            "active_side": "LOAD",
            "fixed_side": "SOURCE",
            "mode_str": "LP",
            "file_prefix": "load",
            "opposite": PullType.SOURCEPULL
        }
    }
    def __init__(self):
        self.driver = AWRDriver()
        self.logger = ResultsLogger()
        self._state_handlers = {
            objects.StateType.ELEMENT: self._handle_element_state,
            objects.StateType.RF_FREQUENCY: self._handle_frequency_state,
        }

    def _handle_element_state(self, config_obj, value):
        for elem in config_obj.element:
            self.driver.configure_element(elem.name, {elem.arg: str(value)})

    def _handle_frequency_state(self, config_obj, value):
        self.driver.set_frequency(float(value))

    def _apply_configuration(self, config_obj, value):
        handler = self._state_handlers.get(config_obj.type)
        if handler:
            handler(config_obj, value)
        else:
            logger.error(f"Unsupported StateType: {config_obj.type}")

    def _build_tuner_params(self, side: str, mag: Any, ang: Any, harmonic: int = 1) -> dict:
        cfg = TUNER_SETTINGS[side]
        return {
            f"{cfg['prefix_mag']}{harmonic}": str(mag),
            f"{cfg['prefix_ang']}{harmonic}": str(ang)
        }

    def _run_iteration(self, iter_idx: int, pull_type: PullType,
                       radius: float, sweep_center: Tuple[float, float],
                       fixed_pos: Tuple[float, float]) -> objects.PullResult:
        """Executes a single Source or Load pull step."""

        is_source = (pull_type == PullType.SOURCEPULL)
        h_idx = 1

        active_side = "SOURCE" if is_source else "LOAD"
        fixed_side = "LOAD" if is_source else "SOURCE"

        # Apply Tuner Settings
        active_params = self._build_tuner_params(active_side, "calcMag(50,0,z0)", "calcAng(50,0,z0)", h_idx)
        fixed_params = self._build_tuner_params(fixed_side, fixed_pos[0], fixed_pos[1], h_idx)

        self.driver.configure_element(TUNER_SETTINGS["SOURCE"]["name"], active_params if is_source else fixed_params)
        self.driver.configure_element(TUNER_SETTINGS["LOAD"]["name"], fixed_params if is_source else active_params)

        # Configure Load-Pull Wizard
        wizard_opts = {
            "LP_MaxHarmonic": h_idx,
            "LP_DataFileName": f"{active_side.lower()}_data_{iter_idx}",
            "LP_OverwriteDataFile": True,
            f"LP_Sweep_{active_side.capitalize()}{h_idx}": True,
            f"LP_Sweep_{fixed_side.capitalize()}{h_idx}": False,
            f"LP_{active_side.capitalize()}{h_idx}_Density": "Extra fine",
            f"LP_{active_side.capitalize()}{h_idx}_Radius": radius,
            f"LP_{active_side.capitalize()}{h_idx}_CenterMagnitude": sweep_center[0],
            f"LP_{active_side.capitalize()}{h_idx}_CenterAngle": sweep_center[1]
        }

        self.driver.run_wizard(wizard_opts)

        graph_name = GRAPH_NAME_PATTERN.format(iter=iter_idx, type=active_side.lower())
        point, mag, ang = POINT_SELECTOR.select_point(self.driver, graph_name)

        return objects.PullResult(iter_no=iter_idx, mode="SP" if is_source else "LP",
                                  point=point, mag=mag, ang=ang)

    def _finalize_state(self, results: List[objects.PullResult]) -> Tuple[Dict, Tuple]:
        """Finalizes state by setting optimal impedances and fetching measurements."""
        lp_results = [x for x in results if x.mode == "LP"]
        best_lp = FINAL_STRATEGY.find_best(lp_results)
        best_sp = next(res for res in results if res.iter_no == best_lp.iter_no and res.mode == "SP")

        # Set optimal positions
        self.driver.configure_element(TUNER_SETTINGS["SOURCE"]["name"], self._build_tuner_params("SOURCE", best_sp.mag, best_sp.ang))
        self.driver.configure_element(TUNER_SETTINGS["LOAD"]["name"], self._build_tuner_params("LOAD", best_lp.mag, best_lp.ang))

        measured_data = {}
        for m in MEASUREMENT_CONFIG:
            data = self.driver.get_marker_data(m["graph"], m["marker"], toggle_enable=True)
            measured_data[m["header"]] = str(data[m["index"]]) if len(data) > m["index"] else "NaN"

        tuner_data = (str(best_sp.mag), str(best_sp.ang), str(best_lp.mag), str(best_lp.ang))
        return measured_data, tuner_data

    def run_state(self, state_values: Tuple):
        """Processes a single combination of state variables."""
        for idx, val in enumerate(state_values):
            self._apply_configuration(STATE_VAR[idx], val)

        current_results = []
        pos = {PullType.SOURCEPULL: (0.0, 0.0), PullType.LOADPULL: (0.0, 0.0)}

        for i in range(ITERATION_COUNT):
            radius = float(RADIUS_LIST[i])

            # Step 1: Source Pull
            sp_res = self._run_iteration(i + 1, PullType.SOURCEPULL, radius, pos[PullType.SOURCEPULL], pos[PullType.LOADPULL])
            current_results.append(sp_res)
            pos[PullType.SOURCEPULL] = (float(sp_res.mag), float(sp_res.ang))

            # Step 2: Load Pull
            lp_res = self._run_iteration(i + 1, PullType.LOADPULL, radius, pos[PullType.LOADPULL], pos[PullType.SOURCEPULL])
            current_results.append(lp_res)
            pos[PullType.LOADPULL] = (float(lp_res.mag), float(lp_res.ang))

        measured_data, tuner_data = self._finalize_state(current_results)
        self.logger.log_state(state_values, current_results, measured_data, tuner_data)

    def start(self):
        """Entry point for the simulation sweep."""
        for cons in STATE_CONS:
            self._apply_configuration(cons, cons.value[0])

        combinations = list(itertools.product(*[v.value for v in STATE_VAR]))
        logger.info(f"Executing {len(combinations)} state combinations.")

        for combo in combinations:
            self.run_state(combo)


def main():
    SimulationManager().start()


if __name__ == "__main__":
    main()
