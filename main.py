import csv
import itertools
import re
import time
from typing import List, Tuple, Any, Dict
from enum import Enum, auto

# Custom Configuration and Objects
from config import *
import objects

# Logger
from logger import LOGGER

# AWR Automation Modules
from pyawr_get_marker_value import get_marker_value
from pyawr_configure_schematic_element import configure_schematic_element
from pyawr_loadpull_wizard import run_loadpull_wizard
from pyawr_configure_schematic_rf_frequency import configure_schematic_rf_frequency

# Global Logger Instance
logger = LOGGER


class PullType(Enum):
    """Enumeration defining the active impedance pull direction."""
    LOADPULL = auto()
    SOURCEPULL = auto()


class AWRDriver:
    """
    Static interface wrapper for AWR Microwave Office API operations.
    Isolates direct API calls from the main simulation logic.
    """

    @staticmethod
    def configure_element(element_name: str, params: dict):
        """Configures a schematic element with the provided parameters."""
        configure_schematic_element(
            schematic_title=SCHEMATIC_NAME,
            target_designator=element_name,
            parameter_map=params,
        )

    @staticmethod
    def set_frequency(freq: float):
        """Updates the system simulation frequency."""
        configure_schematic_rf_frequency(
            schematic_name=SCHEMATIC_NAME,
            frequencies=freq
        )

    @staticmethod
    def get_marker_data(graph: str, marker: str, toggle_enable: bool = False) -> List[float]:
        """
        Retrieves numerical data from a graph marker.

        Returns:
            List[float]: Extracted numerical values (e.g., [Mag, Ang]).
                         Returns a list of zeros if retrieval fails.
        """
        raw_output = get_marker_value(
            graph_title=graph,
            marker_designator=marker,
            perform_simulation=True,
            toggle_enable=toggle_enable
        )

        if not raw_output:
            return [0.0, 0.0, 0.0]

        # Extract floating point numbers using regex
        numbers = re.findall(r"-?\d+\.?\d*", raw_output)
        return [float(n) for n in numbers]

    @staticmethod
    def run_wizard(options: dict):
        """Triggers the Load Pull Wizard with the specified configuration."""
        run_loadpull_wizard(options)


class ResultsLogger:
    """
    Manages CSV file operations, including header generation and row persistence.
    """

    def __init__(self, filename=FILENAME):
        self.filename = filename
        self.headers = self._generate_headers()
        self._init_file()

    def _generate_headers(self) -> List[str]:
        """Generates the complete list of column headers for the results file."""
        headers = [var.name for var in STATE_VAR]
        headers.extend([m["header"] for m in MEASUREMENT_CONFIG])
        headers.extend(["Best_Source_Mag", "Best_Source_Ang", "Best_Load_Mag", "Best_Load_Ang"])

        for i in range(ITERATION_COUNT):
            for mode in ["SP", "LP"]:
                prefix = f"{mode}_It{i + 1}"
                headers.extend([f"{prefix}_Point", f"{prefix}_Mag", f"{prefix}_Ang"])

        return headers

    def _init_file(self):
        """Creates the CSV file and writes the header row."""
        try:
            with open(self.filename, mode='w', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow(self.headers)
            logger.info(f"Storage Initialized: '{self.filename}'")
        except IOError as e:
            logger.critical(f"Failed to initialize storage file: {e}")
            raise

    def log_state(self, state_values: Tuple, results: List[Any], measured_data: dict, best_tuner_data: Tuple):
        """Appends a single simulation result row to the CSV."""
        measured_row = [measured_data[m["header"]] for m in MEASUREMENT_CONFIG]
        row = list(state_values) + measured_row + list(best_tuner_data)

        for res in results:
            row.extend([res.point, res.mag, res.ang])

        try:
            with open(self.filename, mode='a', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow(row)
        except IOError as e:
            logger.error(f"Failed to write data row: {e}")


class SimulationManager:
    """
    Core logic controller for the multi-iteration load-pull simulation.
    Handles state management, optimization loops, and result aggregation.
    """

    def __init__(self):
        self.driver = AWRDriver()
        self.logger = ResultsLogger()
        self._state_handlers = {
            objects.StateType.ELEMENT: self._handle_element_state,
            objects.StateType.RF_FREQUENCY: self._handle_frequency_state,
        }

    def _handle_element_state(self, config_obj, value):
        """Updates schematic elements based on the state variable."""
        for elem in config_obj.element:
            self.driver.configure_element(elem.name, {elem.arg: str(value)})

    def _handle_frequency_state(self, config_obj, value):
        """Updates the system frequency based on the state variable."""
        self.driver.set_frequency(float(value))

    def _apply_configuration(self, config_obj, value):
        """Dispatches the configuration to the appropriate handler."""
        handler = self._state_handlers.get(config_obj.type)
        if handler:
            handler(config_obj, value)
        else:
            logger.error(f"Unsupported StateType encountered: {config_obj.type}")

    def _build_tuner_params(self, side: str, mag: Any, ang: Any, harmonic: int = 1) -> dict:
        """Helper to format tuner parameters for AWR."""
        cfg = TUNER_SETTINGS[side]
        return {
            f"{cfg['prefix_mag']}{harmonic}": str(mag),
            f"{cfg['prefix_ang']}{harmonic}": str(ang)
        }

    def _run_iteration(self, iter_idx: int, pull_type: PullType,
                       radius: float, sweep_center: Tuple[float, float],
                       fixed_pos: Tuple[float, float]) -> objects.PullResult:
        """
        Executes a single Source or Load pull iteration step.
        Configures the tuners, runs the wizard, and selects the optimal point.
        """
        is_source = (pull_type == PullType.SOURCEPULL)
        h_idx = 1

        active_side = "SOURCE" if is_source else "LOAD"
        fixed_side = "LOAD" if is_source else "SOURCE"

        # Configure active side for sweeping and fixed side to hold position
        active_params = self._build_tuner_params(active_side, "calcMag(50,0,z0)", "calcAng(50,0,z0)", h_idx)
        fixed_params = self._build_tuner_params(fixed_side, fixed_pos[0], fixed_pos[1], h_idx)

        self.driver.configure_element(TUNER_SETTINGS["SOURCE"]["name"], active_params if is_source else fixed_params)
        self.driver.configure_element(TUNER_SETTINGS["LOAD"]["name"], fixed_params if is_source else active_params)

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

        # Immediate float conversion ensures data integrity
        return objects.PullResult(
            iter_no=iter_idx,
            mode="SP" if is_source else "LP",
            point=point,
            mag=float(mag),
            ang=float(ang)
        )

    def _finalize_state(self, results: List[objects.PullResult]) -> Tuple[Dict, Tuple]:
        """
        Identifies the global maximum results, sets the tuners, and captures final measurements.
        """
        # Find the iteration with the highest performance metric
        best_lp = max((x for x in results if x.mode == "LP"), key=lambda x: float(x.point))

        # Find the corresponding Source Pull result
        best_sp = next(res for res in results
                       if res.iter_no == best_lp.iter_no and res.mode == "SP")

        self.driver.configure_element(TUNER_SETTINGS["SOURCE"]["name"],
                                      self._build_tuner_params("SOURCE", best_sp.mag, best_sp.ang))
        self.driver.configure_element(TUNER_SETTINGS["LOAD"]["name"],
                                      self._build_tuner_params("LOAD", best_lp.mag, best_lp.ang))

        measured_data = {}
        for m in MEASUREMENT_CONFIG:
            data = self.driver.get_marker_data(m["graph"], m["marker"], toggle_enable=True)
            val = str(data[m["index"]]) if len(data) > m["index"] else "NaN"
            measured_data[m["header"]] = val

        tuner_data = (str(best_sp.mag), str(best_sp.ang),
                      str(best_lp.mag), str(best_lp.ang))

        return measured_data, tuner_data

    def run_state(self, state_values: Tuple, state_idx: int = 1, total_states: int = 1):
        """
        Executes the optimization loop for a single combination of state variables.
        """
        # Header Log: Indicates the start of a new state block
        logger.info(f">>> PROCESSING STATE {state_idx}/{total_states}: {state_values}")

        for idx, val in enumerate(state_values):
            self._apply_configuration(STATE_VAR[idx], val)

        current_results = []
        pos = {PullType.SOURCEPULL: (0.0, 0.0), PullType.LOADPULL: (0.0, 0.0)}

        for i in range(ITERATION_COUNT):
            radius = float(RADIUS_LIST[i])
            iter_num = i + 1

            # Sub-header Log: Indicates the start of an iteration within the state
            logger.info(f"   > Iteration {iter_num}/{ITERATION_COUNT} (Radius: {radius})")

            # Source Pull Step
            sp_res = self._run_iteration(
                iter_num, PullType.SOURCEPULL, radius,
                pos[PullType.SOURCEPULL], pos[PullType.LOADPULL]
            )
            current_results.append(sp_res)
            pos[PullType.SOURCEPULL] = (float(sp_res.mag), float(sp_res.ang))

            # Result Log: Bullet point style for clarity
            logger.info(f"     * SP Result: Mag [{sp_res.mag:.3f}], Ang [{sp_res.ang:.1f}]")

            # Load Pull Step
            lp_res = self._run_iteration(
                iter_num, PullType.LOADPULL, radius,
                pos[PullType.LOADPULL], pos[PullType.SOURCEPULL]
            )
            current_results.append(lp_res)
            pos[PullType.LOADPULL] = (float(lp_res.mag), float(lp_res.ang))

            # Result Log: Bullet point style for clarity
            logger.info(f"     * LP Result: Mag [{lp_res.mag:.3f}], Ang [{lp_res.ang:.1f}]")

        logger.debug(f"   > Finalizing state configuration...")

        measured_data, tuner_data = self._finalize_state(current_results)
        self.logger.log_state(state_values, current_results, measured_data, tuner_data)

        # Footer log: Indicates the completion of the state block
        logger.info(f"<<< STATE {state_idx} COMPLETE")
        return measured_data

    def start(self):
        """
        Main entry point. Generates the state matrix and starts the simulation sequence.
        """
        logger.info("Starting Simulation Sequence")

        for constant in STATE_CONS:
            self._apply_configuration(constant, constant.value[0])

        combinations = list(itertools.product(*[v.value for v in STATE_VAR]))
        total_combos = len(combinations)

        logger.info(f"State Matrix Generated: {total_combos} unique combinations.")

        start_time = time.time()

        for idx, combo in enumerate(combinations):
            self.run_state(combo, state_idx=idx + 1, total_states=total_combos)

        elapsed_time = time.time() - start_time
        logger.info(f"Simulation Sequence Completed in {elapsed_time:.2f} seconds.")


def main():
    try:
        engine = SimulationManager()
        engine.start()
    except KeyboardInterrupt:
        logger.warning("Simulation interrupted by user.")
    except Exception as e:
        logger.critical(f"Unhandled Exception in Main Loop: {e}")
        raise


if __name__ == "__main__":
    main()