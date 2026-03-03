"""
manager.py
Acts as the domain controller for the Load-Pull operations.
Orchestrates the sequence execution using the structured LoadPullConfig.
Strictly adheres to the tree-branch logging hierarchy and testing protocols.
"""

from typing import Any, Tuple, Dict, List
from dataclasses import dataclass
from rfdesign.loadpull.models import PullResult
from core.logger import logger

from rfdesign.loadpull.handlers import HandlersConfig
from rfdesign.loadpull.sequence import SequenceConfig, LoadPullSequence


@dataclass
class LoadPullConfig:
    """Master configuration node for the entire LoadPull domain."""
    handlers: HandlersConfig
    sequence: SequenceConfig


class LoadPullManager:
    """
    Manages load-pull specific processes and delegates tasks to the sequence handler.
    Operates strictly via the injected LoadPullConfig branch.
    """

    def __init__(self, driver: Any, exporter: Any, config: LoadPullConfig):
        self.driver = driver
        self.exporter = exporter
        self.config = config

        self.sequence = LoadPullSequence(
            driver=self.driver,
            exporter=self.exporter,
            config=self.config.sequence
        )

    def execute_sequence(self, export_subpath: str) -> Tuple[Dict, List[PullResult], Tuple]:
        logger.info("│   ├── Initiating Load-Pull Sequence...")
        return self.sequence.execute(export_subpath)

