"""
main.py
Core entry point for the AWR Automation sequence.
Orchestrates the simulation drivers, state managers, and delegates specific
engineering analyses (e.g., Load-Pull) to specialized sequence modules.
"""

import itertools
import time
import os
from typing import List, Tuple, Any, Dict, Protocol, Union

# Custom Configuration and Objects
from config import *

# Logger and Exporter
from logger.logger import LOGGER
from dataexporter.dataexporter import DataExporter

# Drivers and Handlers
from awr.awr_driver import AWRDriver
from rfdesign.loadpull.manager import LoadPullManager


class ICircuitManager(Protocol):
    def configure_element(self, schematic_name: str, element_name: str, params: Dict[str, Any]) -> None: ...
    def set_frequency(self, schematic_name: str, freq: Union[float, List[float]]) -> None: ...


class IGraphManager(Protocol):
    def get_marker_data(self, graph: str, marker: str, toggle_enable: bool = False) -> List[float]: ...


class IWizardManager(Protocol):
    def run_wizard(self, options: Dict[str, Any]) -> None: ...


class IProjectManager(Protocol):
    def save_current_project_as(self, save_path: str) -> None: ...
    def open_existing_project(self, project_path: str) -> bool: ...


class ISimulatorDriver(Protocol):
    project: IProjectManager
    circuit: ICircuitManager
    graph: IGraphManager
    wizard: IWizardManager


class SimulationManager:
    """
    Core logic controller that handles global state management, optimization loops,
    and delegates specialized simulations to strategy modules.
    """

    def __init__(self, driver: ISimulatorDriver):
        self.driver = driver

        # Initialize the decoupled DataExporter targeting the dynamic run directory
        self.exporter = DataExporter(base_directory=RUN_DIR)

        # Encapsulate Load-Pull configuration parameters
        lp_config = {
            "schematic_name": SCHEMATIC_NAME,
            "tuner_settings": TUNER_SETTINGS,
            "measurement_config": MEASUREMENT_CONFIG,
            "graph_name_pattern": GRAPH_NAME_PATTERN,
            "point_selector": POINT_SELECTOR,
            "iteration_count": ITERATION_COUNT,
            "radius_list": RADIUS_LIST
        }

        # Initialize the Load-Pull Manager via dependency injection
        self.loadpull_manager = LoadPullManager(
            driver=self.driver,
            exporter=self.exporter,
            config_params=lp_config
        )
        # Generate domain-specific headers and initialize the persistence layer
        initial_headers = self._generate_csv_headers()
        csv_subpath = os.path.join("csv results", "simulation_results.csv")
        self.exporter.initialize_csv(csv_subpath, initial_headers)

    def _generate_csv_headers(self) -> List[str]:
        """
        Generates the column headers for the results file.
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

    def run_state(self, state_values: Tuple, state_idx: int = 1, total_states: int = 1):
        """
        Executes the overarching logic for a single combination of state variables.
        """
        LOGGER.info(f"├── PROCESSING STATE {state_idx}/{total_states}: {state_values}")

        state_dir_name = f"State No {state_idx}"

        current_state_graph_dir = os.path.join(GRAPHS_DIR, state_dir_name)
        if not os.path.exists(current_state_graph_dir):
            os.makedirs(current_state_graph_dir)
            LOGGER.debug(f"│   ├── Created graph directory: {current_state_graph_dir}")

        current_state_emp_dir = os.path.join(EMP_DIR, state_dir_name)
        if not os.path.exists(current_state_emp_dir):
            os.makedirs(current_state_emp_dir)
            LOGGER.debug(f"│   ├── Created EMP directory: {current_state_emp_dir}")

        export_subpath = os.path.join("graphs", state_dir_name)

        # Apply State Variables via LoadPull Manager
        for idx, val in enumerate(state_values):
            self.loadpull_manager.apply_state(STATE_VAR[idx], val)

        # Delegate the actual simulation iterations to the LoadPull Manager
        measured_data, current_results, tuner_data = self.loadpull_manager.execute_sequence(export_subpath)

        # Compile and persist the row data
        measured_row = [measured_data[m["header"]] for m in MEASUREMENT_CONFIG]
        row_data = [state_idx] + list(state_values) + measured_row + list(tuner_data)

        for res in current_results:
            row_data.extend([res.point, res.mag, res.ang])

        csv_subpath = os.path.join("csv results", "simulation_results.csv")
        self.exporter.append_csv_row(csv_subpath, row_data)

        emp_filename = f"simulation_state_{state_idx}.emp"
        full_emp_path = os.path.join(current_state_emp_dir, emp_filename)
        self.driver.project.save_current_project_as(full_emp_path)

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

            self.loadpull_manager.apply_state(constant, actual_val)

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
        selected_driver = AWRDriver(exe_path=AWR_PATH)

        LOGGER.info("├── Loading Project Template...")
        if not selected_driver.project.open_existing_project(PROJECT_TEMPLATE_PATH):
            LOGGER.critical("└── Failed to load project template. Aborting sequence.")
            return

        engine = SimulationManager(driver=selected_driver)
        engine.start()

    except KeyboardInterrupt:
        LOGGER.warning("└── Simulation interrupted by user intervention.")
    except Exception as e:
        LOGGER.critical(f"└── Unhandled Exception in Main Loop: {e}")
        raise


if __name__ == "__main__":
    main()