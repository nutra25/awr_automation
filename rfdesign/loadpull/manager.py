"""
manager.py (Load-Pull Domain)
Acts as a facade for all load-pull specific operations, encapsulating
state handling, sequencing, and point selection strategies.
"""

from typing import Dict, Any, Tuple, List

# Importing specialized domain logic
from rfdesign.loadpull.handlers import StateHandler
from rfdesign.loadpull.sequence import LoadPullSequence

class LoadPullManager:
    """
    Manages high-level Load-Pull operations by delegating to specialized
    sequence and state handler modules, ensuring clean architecture.
    """
    def __init__(self, driver: Any, exporter: Any, config_params: Dict[str, Any]):
        self.driver = driver
        self.exporter = exporter

        # Extract configuration safely
        schematic_name = config_params.get("schematic_name")

        # Initialize State Handler
        self.state_handler = StateHandler(
            circuit_manager=self.driver.circuit,
            schematic_name=schematic_name
        )

        # Initialize Sequence Strategy
        self.sequence = LoadPullSequence(
            driver=self.driver,
            exporter=self.exporter,
            schematic_name=schematic_name,
            tuner_settings=config_params.get("tuner_settings"),
            measurement_config=config_params.get("measurement_config"),
            graph_name_pattern=config_params.get("graph_name_pattern"),
            point_selector=config_params.get("point_selector"),
            iteration_count=config_params.get("iteration_count"),
            radius_list=config_params.get("radius_list")
        )

    def apply_state(self, config_obj: Any, value: Any) -> None:
        """
        Delegates configuration application to the StateHandler.
        """
        self.state_handler.apply_configuration(config_obj, value)

    def execute_sequence(self, export_subpath: str) -> Tuple[Dict, List, Tuple]:
        """
        Delegates the iterative simulation loop to the LoadPullSequence.
        """
        return self.sequence.execute(export_subpath)