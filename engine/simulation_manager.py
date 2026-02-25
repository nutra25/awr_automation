"""
simulation_manager.py
Core engine for the AWR Automation sequence.
Handles global state management, optimization loops, and delegates specialized
engineering analyses to strategy modules within the rfdesign domain.
"""

import itertools
import time
import os
from typing import List, Tuple, Any, Dict, Protocol, Union

from config import *
from logger.logger import LOGGER
from dataexporter.dataexporter import DataExporter

# Assuming handlers and sequence are now routed through your new loadpull manager
from rfdesign.loadpull.handlers import StateHandler
from rfdesign.loadpull.manager import LoadPullManager # Adjusted to your new structure


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
    Orchestrates the global execution state and delegates domain-specific tasks.
    """

    def __init__(self, driver: ISimulatorDriver):
        self.driver = driver
        self.exporter = DataExporter(base_directory=RUN_DIR)

        # Initialize the state handler
        self.state_handler = StateHandler(
            circuit_manager=self.driver.circuit,
            schematic_name=SCHEMATIC_NAME
        )

        # Initialize the Load-Pull Domain Manager
        self.lp_manager = LoadPullManager(
            driver=self.driver,
            exporter=self.exporter,
            schematic_name=SCHEMATIC_NAME,
            tuner_settings=TUNER_SETTINGS,
            measurement_config=MEASUREMENT_CONFIG,
            graph_name_pattern=GRAPH_NAME_PATTERN,
            point_selector=POINT_SELECTOR,
            iteration_count=ITERATION_COUNT,
            radius_list=RADIUS_LIST
        )

        # Initialize CSV
        initial_headers = self._generate_csv_headers()
        csv_subpath = os.path.join("csv results", "simulation_results.csv")
        self.exporter.initialize_csv(csv_subpath, initial_headers)

    def _generate_csv_headers(self) -> List[str]:
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
        LOGGER.info(f"├── PROCESSING STATE {state_idx}/{total_states}: {state_values}")

        state_dir_name = f"State No {state_idx}"
        current_state_graph_dir = os.path.join(GRAPHS_DIR, state_dir_name)
        current_state_emp_dir = os.path.join(EMP_DIR, state_dir_name)

        os.makedirs(current_state_graph_dir, exist_ok=True)
        os.makedirs(current_state_emp_dir, exist_ok=True)

        export_subpath = os.path.join("graphs", state_dir_name)

        # Apply Global State Configurations
        for idx, val in enumerate(state_values):
            self.state_handler.apply_configuration(STATE_VAR[idx], val)

        # Delegate execution to the Load-Pull Manager
        measured_data, current_results, tuner_data = self.lp_manager.execute_sequence(export_subpath)

        # Data Persistence
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
        LOGGER.info("Starting Global Simulation Sequence")

        for constant in STATE_CONS:
            val = constant.value
            actual_val = val[0] if isinstance(val, (list, tuple)) and len(val) == 1 else val
            self.state_handler.apply_configuration(constant, actual_val)

        combinations = list(itertools.product(*[v.value for v in STATE_VAR]))
        total_combos = len(combinations)

        LOGGER.info(f"├── State Matrix Generated: {total_combos} unique combinations.")

        start_time = time.time()
        for idx, combo in enumerate(combinations):
            self.run_state(combo, state_idx=idx + 1, total_states=total_combos)

        elapsed_time = time.time() - start_time
        LOGGER.info(f"└── Global Simulation Sequence Completed in {elapsed_time:.2f} seconds.")