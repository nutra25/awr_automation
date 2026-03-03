"""
manager.py
Acts as the domain controller for the Load-Pull operations.
Orchestrates the sequence execution using the structured LoadPullConfig.
Strictly adheres to the tree-branch logging hierarchy and testing protocols.
"""

from typing import Any, Tuple, Dict, List
from pydantic import BaseModel, ConfigDict
from rfdesign.loadpull.models import PullResult
from core.logger import logger

from rfdesign.loadpull.handlers import HandlersConfig
from rfdesign.loadpull.sequence import SequenceConfig, LoadPullSequence


class LoadPullConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    handlers: HandlersConfig
    sequence: SequenceConfig


class LoadPullManager:
    """
    Manages load-pull specific processes and delegates tasks to the sequence handler.
    Operates strictly via the injected Context architecture.
    """

    def __init__(self, context: Any):
        self.context = context
        self.driver = self.context.driver
        self.exporter = self.context.exporter

        self.config = self.context.config.rf_design.loadpull

        self.sequence = LoadPullSequence(context=self.context)

    def execute_sequence(self, export_subpath: str) -> Tuple[Dict, List[PullResult], Tuple]:
        logger.info("│   ├── Initiating Load-Pull Sequence...")
        return self.sequence.execute(export_subpath)