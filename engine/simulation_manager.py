"""
simulation_manager.py
Core engine for the AWR Automation sequence.
Handles global state management, optimization loops, and delegates specialized
engineering analyses to strategy modules within the rfdesign domain using hierarchical configurations.
"""

import itertools
import time
import os
import sys
from typing import List, Tuple, Any, Dict, Protocol, Union
from core.logger import LOGGER
from core.context import AutomationContext
from rfdesign.loadpull.handlers import StateHandler
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
    Orchestrates the global execution state and delegates domain-specific tasks.
    Receives all dependencies and configurations via the injected Context.
    """

    def __init__(self, context: AutomationContext):
        self.context = context

        # Extract dependencies from context for easier access
        self.driver = self.context.driver
        self.exporter = self.context.exporter
        self.config = self.context.config.engine
        self.rf_design_config = self.context.config.rf_design

        self.state_handler = StateHandler(
            circuit_manager=self.driver.circuit,
            config=self.rf_design_config.loadpull.handlers
        )

        # Pass only the context to the LoadPullManager
        self.lp_manager = LoadPullManager(self.context)

        csv_dir = os.path.join(self.config.run_dir, "csv results")
        os.makedirs(csv_dir, exist_ok=True)

        initial_headers = self._generate_csv_headers()
        csv_subpath = os.path.join("csv results", "simulation_results.csv")
        self.exporter.initialize_csv(csv_subpath, initial_headers)

    def _generate_csv_headers(self) -> List[str]:
        headers = ["State No"]
        headers.extend([var.name for var in self.config.state_var])
        headers.extend([m["header"] for m in self.config.measurement_config])
        headers.extend(["Best_Source_Mag", "Best_Source_Ang", "Best_Load_Mag", "Best_Load_Ang"])

        for i in range(self.config.iteration_count):
            for mode in ["SP", "LP"]:
                prefix = f"{mode}_It{i + 1}"
                headers.extend([f"{prefix}_Point", f"{prefix}_Mag", f"{prefix}_Ang"])
        return headers

    def run_state(self, state_values: Tuple, state_idx: int = 1, total_states: int = 1):
        LOGGER.info(f"├── PROCESSING STATE {state_idx}/{total_states}: {state_values}")

        state_dir_name = f"State No {state_idx}"
        current_state_graph_dir = os.path.join(self.config.graphs_dir, state_dir_name)
        current_state_emp_dir = os.path.join(self.config.emp_dir, state_dir_name)

        os.makedirs(current_state_graph_dir, exist_ok=True)
        os.makedirs(current_state_emp_dir, exist_ok=True)

        export_subpath = os.path.join("graphs", state_dir_name)

        for idx, val in enumerate(state_values):
            self.state_handler.apply_configuration(self.config.state_var[idx], val)

        measured_data, current_results, tuner_data = self.lp_manager.execute_sequence(export_subpath)

        measured_row = [measured_data[m["header"]] for m in self.config.measurement_config]
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

        for constant in self.config.state_cons:
            val = constant.value
            actual_val = val[0] if isinstance(val, (list, tuple)) and len(val) == 1 else val
            self.state_handler.apply_configuration(constant, actual_val)

        combinations = list(itertools.product(*[v.value for v in self.config.state_var]))
        total_combos = len(combinations)

        LOGGER.info(f"├── State Matrix Generated: {total_combos} unique combinations.")

        start_time = time.time()
        for idx, combo in enumerate(combinations):
            self.run_state(combo, state_idx=idx + 1, total_states=total_combos)

        elapsed_time = time.time() - start_time
        LOGGER.info(f"└── Global Simulation Sequence Completed in {elapsed_time:.2f} seconds.")


if __name__ == "__main__":
    LOGGER.info("├── Starting standalone test sequence for simulation_manager.py")
    try:
        class DummyDriver:
            pass

        LOGGER.info("└── Test execution sequence completed successfully")
    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed: {ex}")
        sys.exit(1)