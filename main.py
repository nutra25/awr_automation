"""
main.py
Core entry point for the AWR Load-Pull Automation sequence.
Orchestrates the simulation drivers, state managers, and data exporters.
"""

import itertools
import time
import os
from typing import List, Tuple, Any, Dict, Protocol, Union
from enum import Enum, auto

# Custom Configuration and Objects
from config import *
import objects

# Logger and Exporter
from logger.logger import LOGGER
from dataexporter.dataexporter import DataExporter

# Drivers
from awr.awr_driver import AWRDriver


class PullType(Enum):
    """Enumeration defining the active impedance pull direction."""
    LOADPULL = auto()
    SOURCEPULL = auto()


class ISimulatorDriver(Protocol):
    """
    A protocol defining the necessary interface for simulation drivers.
    Any implementing driver class must adhere to these structural rules.
    """
    def configure_element(self, element_name: str, params: Dict[str, Any]) -> None:
        ...

    def set_frequency(self, freq: Union[float, List[float]]) -> None:
        ...

    def get_marker_data(self, graph: str, marker: str, toggle_enable: bool = False) -> List[float]:
        ...

    def run_wizard(self, options: Dict[str, Any]) -> None:
        ...

    def save_current_project_as(self, save_path: str) -> None:
        ...

    def open_existing_project(self, project_path: str) -> bool:
        ...


class SimulationManager:
    """
    Core logic controller for the multi-iteration load-pull simulation.
    Handles state management, optimization loops, and delegates data persistence.
    """

    def __init__(self, driver: ISimulatorDriver):
        self.driver = driver

        # Initialize the decoupled DataExporter targeting the dynamic run directory
        self.exporter = DataExporter(base_directory=RUN_DIR)

        # Generate domain-specific headers and initialize the persistence layer
        initial_headers = self._generate_csv_headers()

        # Provide the relative path for the CSV file initialization
        csv_subpath = os.path.join("csv results", "simulation_results.csv")
        self.exporter.initialize_csv(csv_subpath, initial_headers)

        self._state_handlers = {
            objects.StateType.ELEMENT: self._handle_element_state,
            objects.StateType.RF_FREQUENCY: self._handle_frequency_state,
        }

    def _generate_csv_headers(self) -> List[str]:
        """
        Generates the domain-specific column headers for the results file.
        This logic is maintained here as it is strictly tied to the AWR domain.
        """
        headers = ["State No"]
        headers.extend([var.name for var in STATE_VAR])
        headers.extend([m["header"] for m in MEASUREMENT_CONFIG])
        headers.extend(["Best_Source_Mag", "Best_Source_Ang", "Best_Load_Mag", "Best_Load_Ang"])

        for i in range(ITERATION_COUNT):
            for mode in ["SP", "LP"]:
                prefix = f"{mode}_It{i + 1}"
                headers.extend([f"{prefix}_Point", f"{prefix}_Mag", f"{prefix}_Ang"])
        return headers

    def _handle_element_state(self, config_obj, value):
        """Updates schematic elements based on the state variable."""
        for elem in config_obj.element:
            self.driver.configure_element(elem.name, {elem.arg: str(value)})

    def _handle_frequency_state(self, config_obj, value):
        """Updates the system frequency based on the state variable."""
        if isinstance(value, (list, tuple)):
            freq_val = [float(v) for v in value]
        else:
            freq_val = float(value)
        self.driver.set_frequency(freq_val)

    def _apply_configuration(self, config_obj, value):
        """Dispatches the configuration to the appropriate handler."""
        handler = self._state_handlers.get(config_obj.type)
        if handler:
            handler(config_obj, value)
        else:
            LOGGER.error(f"├── Unsupported StateType encountered: {config_obj.type}")

    def _build_tuner_params(self, side: str, mag: Any, ang: Any, harmonic: int = 1) -> dict:
        """Helper to format tuner parameters for AWR."""
        cfg = TUNER_SETTINGS[side]
        return {
            f"{cfg['prefix_mag']}{harmonic}": str(mag),
            f"{cfg['prefix_ang']}{harmonic}": str(ang)
        }

    def _run_iteration(self, iter_idx: int, pull_type: PullType,
                       radius: float, sweep_center: Tuple[float, float],
                       fixed_pos: Tuple[float, float], export_subpath: str) -> objects.PullResult:
        """
        Executes a single Source or Load pull iteration step.
        Configures the tuners, runs the wizard, and delegates graphic export via the point selector.
        """
        is_source = (pull_type == PullType.SOURCEPULL)
        h_idx = 1
        active_side = "SOURCE" if is_source else "LOAD"
        fixed_side = "LOAD" if is_source else "SOURCE"

        active_params = self._build_tuner_params(active_side, "calcMag(50,0,z0)", "calcAng(50,0,z0)", h_idx)

        if isinstance(fixed_pos, (list, tuple)) and len(fixed_pos) >= 2:
            fixed_params = self._build_tuner_params(fixed_side, fixed_pos[0], fixed_pos[1], h_idx)
            center_ang = sweep_center[1] if isinstance(sweep_center, (list, tuple)) and len(sweep_center) >= 2 else sweep_center
        else:
            fixed_params = self._build_tuner_params(fixed_side, fixed_pos, fixed_pos, h_idx)
            center_ang = sweep_center

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
            f"LP_{active_side.capitalize()}{h_idx}_CenterMagnitude": sweep_center[0] if isinstance(sweep_center, (list, tuple)) else sweep_center,
            f"LP_{active_side.capitalize()}{h_idx}_CenterAngle": center_ang
        }

        self.driver.run_wizard(wizard_opts)

        graph_name = GRAPH_NAME_PATTERN.format(iter=iter_idx, type=active_side.lower())

        # Pass the global exporter and the current relative subpath to the point selector
        point, mag, ang = POINT_SELECTOR.select_point(
            self.driver,
            graph_name,
            exporter=self.exporter,
            export_subpath=export_subpath
        )

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
        best_lp = max((x for x in results if x.mode == "LP"), key=lambda x: float(x.point))
        best_sp = next(res for res in results if res.iter_no == best_lp.iter_no and res.mode == "SP")

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
        Executes the optimization loop for a single combination of state variables
        and delegates the resulting data array to the persistence module.
        """
        LOGGER.info(f"├── PROCESSING STATE {state_idx}/{total_states}: {state_values}")

        state_dir_name = f"State No {state_idx}"

        # Ensure the directories exist before passing the path to the exporter
        current_state_graph_dir = os.path.join(GRAPHS_DIR, state_dir_name)
        if not os.path.exists(current_state_graph_dir):
            os.makedirs(current_state_graph_dir)
            LOGGER.debug(f"│   ├── Created graph directory: {current_state_graph_dir}")

        current_state_emp_dir = os.path.join(EMP_DIR, state_dir_name)
        if not os.path.exists(current_state_emp_dir):
            os.makedirs(current_state_emp_dir)
            LOGGER.debug(f"│   ├── Created EMP directory: {current_state_emp_dir}")

        # Define the relative path to be used by the DataExporter for graphic artifacts
        export_subpath = os.path.join("graphs", state_dir_name)

        for idx, val in enumerate(state_values):
            self._apply_configuration(STATE_VAR[idx], val)

        current_results = []
        pos = {PullType.SOURCEPULL: (0.0, 0.0), PullType.LOADPULL: (0.0, 0.0)}

        for i in range(ITERATION_COUNT):
            radius = float(RADIUS_LIST[i])
            iter_num = i + 1

            LOGGER.info(f"│   ├── Iteration {iter_num}/{ITERATION_COUNT} (Radius: {radius})")

            sp_res = self._run_iteration(
                iter_num, PullType.SOURCEPULL, radius,
                pos[PullType.SOURCEPULL], pos[PullType.LOADPULL],
                export_subpath
            )
            current_results.append(sp_res)
            pos[PullType.SOURCEPULL] = (float(sp_res.mag), float(sp_res.ang))
            LOGGER.info(f"│   ├── SP Result: Mag [{sp_res.mag:.3f}], Ang [{sp_res.ang:.1f}]")

            lp_res = self._run_iteration(
                iter_num, PullType.LOADPULL, radius,
                pos[PullType.LOADPULL], pos[PullType.SOURCEPULL],
                export_subpath
            )
            current_results.append(lp_res)
            pos[PullType.LOADPULL] = (float(lp_res.mag), float(lp_res.ang))
            LOGGER.info(f"│   └── LP Result: Mag [{lp_res.mag:.3f}], Ang [{lp_res.ang:.1f}]")

        LOGGER.debug("├── Finalizing state configuration and preparing data export...")
        measured_data, tuner_data = self._finalize_state(current_results)

        # Assemble the final row data for export
        measured_row = [measured_data[m["header"]] for m in MEASUREMENT_CONFIG]
        row_data = [state_idx] + list(state_values) + measured_row + list(tuner_data)

        for res in current_results:
            row_data.extend([res.point, res.mag, res.ang])

        # Delegate the persistence operation to the generic DataExporter with specific file path
        csv_subpath = os.path.join("csv results", "simulation_results.csv")
        self.exporter.append_csv_row(csv_subpath, row_data)

        # AWR project file saving uses the driver wrapper mechanism
        emp_filename = f"simulation_state_{state_idx}.emp"
        full_emp_path = os.path.join(current_state_emp_dir, emp_filename)
        self.driver.save_current_project_as(full_emp_path)

        LOGGER.info(f"└── STATE {state_idx} COMPLETE")
        return measured_data

    def start(self):
        """
        Main entry point. Generates the state matrix and starts the simulation sequence.
        """
        LOGGER.info("Starting Simulation Sequence")

        for constant in STATE_CONS:
            val = constant.value
            if isinstance(val, (list, tuple)):
                actual_val = val[0] if len(val) == 1 else val
            else:
                actual_val = val

            self._apply_configuration(constant, actual_val)

        combinations = list(itertools.product(*[v.value for v in STATE_VAR]))
        total_combos = len(combinations)

        LOGGER.info(f"├── State Matrix Generated: {total_combos} unique combinations.")

        start_time = time.time()
        for idx, combo in enumerate(combinations):
            self.run_state(combo, state_idx=idx + 1, total_states=total_combos)

        elapsed_time = time.time() - start_time
        LOGGER.info(f"└── Simulation Sequence Completed in {elapsed_time:.2f} seconds.")


def main():
    try:
        # Initialize Driver with Auto-Launch capability using configuration variables
        selected_driver = AWRDriver(exe_path=AWR_PATH)

        # Load the operational project template required for processing
        LOGGER.info("├── Loading Project Template...")
        if not selected_driver.open_existing_project(PROJECT_TEMPLATE_PATH):
            LOGGER.critical("└── Failed to load project template. Aborting sequence.")
            return

        # Start the simulation engine
        engine = SimulationManager(driver=selected_driver)
        engine.start()

    except KeyboardInterrupt:
        LOGGER.warning("└── Simulation interrupted by user intervention.")
    except Exception as e:
        LOGGER.critical(f"└── Unhandled Exception in Main Loop: {e}")
        raise


if __name__ == "__main__":
    main()