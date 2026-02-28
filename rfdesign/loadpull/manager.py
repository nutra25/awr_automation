"""
manager.py
Acts as the domain controller for the Load-Pull operations.
Orchestrates the sequence execution using the structured LoadPullConfig.
"""

from typing import Any, Tuple, Dict, List
import objects
from logger.logger import LOGGER
from config import LoadPullConfig
from rfdesign.loadpull.sequence import LoadPullSequence


class LoadPullManager:
    """
    Manages load-pull specific processes and delegates tasks to the sequence handler.
    Operates strictly via the injected LoadPullConfig branch.
    """

    def __init__(self, driver: Any, exporter: Any, config: LoadPullConfig):
        """
        Initializes the manager and its nested components with the appropriate configuration branch.
        """
        self.driver = driver
        self.exporter = exporter
        self.config = config

        # Instantiate the sequence handler using its specific config branch
        self.sequence = LoadPullSequence(
            driver=self.driver,
            exporter=self.exporter,
            config=self.config.sequence
        )

    def execute_sequence(self, export_subpath: str) -> Tuple[Dict, List[objects.PullResult], Tuple]:
        """
        Triggers the load-pull sequence and returns the collected metrics.
        """
        LOGGER.info("│   ├── Initiating Load-Pull Sequence...")
        return self.sequence.execute(export_subpath)


if __name__ == "__main__":
    import sys
    LOGGER.info("├── Starting standalone test sequence for manager.py")
    try:
        from config import SequenceConfig, HandlersConfig

        dummy_sequence_config = SequenceConfig(
            schematic_name="Test",
            tuner_settings={},
            measurement_config=[],
            graph_name_pattern="",
            point_selector=None,
            iteration_count=1,
            radius_list=("0.5",)
        )
        dummy_handlers_config = HandlersConfig(schematic_name="Test")
        dummy_config = LoadPullConfig(handlers=dummy_handlers_config, sequence=dummy_sequence_config)

        manager = LoadPullManager(driver=None, exporter=None, config=dummy_config)
        LOGGER.info(f"│   ├── Manager Initialized with Config: {manager.config.__class__.__name__}")
        LOGGER.info("└── Test execution sequence completed successfully")
    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed: {ex}")
        sys.exit(1)