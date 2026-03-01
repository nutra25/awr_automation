"""
state_result_selector.py
Defines strategies for selecting the final state result among multiple iterations.
Operates utilizing embedded configuration nodes for strategy parameters.
"""

from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass
from logger.logger import LOGGER
from rfdesign.loadpull.models import PullResult


@dataclass
class ResultSelectorConfig:
    """
    Configuration node containing target parameters for state result selection strategies.
    """
    target_value: float = 40.0


class BestResultStrategy(ABC):
    """
    Abstract base class (Interface) for result selection strategies.
    """
    def __init__(self, config: ResultSelectorConfig):
        self.config = config

    @abstractmethod
    def find_best(self, results: List['PullResult']) -> 'PullResult':
        pass


class MaxPointStrategy(BestResultStrategy):
    """
    Classic Method: Selects the result with the highest 'point' value.
    """

    def find_best(self, results: List['PullResult']) -> 'PullResult':
        LOGGER.info("Executing Strategy: MaxPointStrategy")

        if not results:
            LOGGER.error(" └── Result list is empty; cannot determine the best result.")
            raise ValueError("Result list is empty.")

        best_result = max(results, key=lambda x: float(x.point))

        LOGGER.info(f" ├── Criteria: Highest value found.")
        LOGGER.info(f" └── Selected Result: {best_result.point} (Iter: {best_result.iter_no}, Mode: {best_result.mode})")

        return best_result


class TargetPointStrategy(BestResultStrategy):
    """
    Alternative Method: Selects the result closest to a specific target value
    defined in the configuration structure.
    """

    def find_best(self, results: List['PullResult']) -> 'PullResult':
        target = self.config.target_value
        LOGGER.info(f"Executing Strategy: TargetPointStrategy (Target: {target})")

        if not results:
            LOGGER.error(" └── Result list is empty; cannot determine the best result.")
            raise ValueError("Result list is empty.")

        best_result = min(results, key=lambda x: abs(float(x.point) - target))

        diff = abs(float(best_result.point) - target)
        LOGGER.info(f" ├── Closest match found (Difference: {diff:.4f}).")
        LOGGER.info(f" └── Selected Result: {best_result.point} (Iter: {best_result.iter_no})")

        return best_result


class LastIterationStrategy(BestResultStrategy):
    """
    Iteration Priority Method: Always selects the result from the final iteration.
    """

    def find_best(self, results: List['PullResult']) -> 'PullResult':
        LOGGER.info("Executing Strategy: LastIterationStrategy")

        if not results:
            LOGGER.error(" └── Result list is empty; cannot determine the best result.")
            raise ValueError("Result list is empty.")

        max_iter = max(results, key=lambda x: x.iter_no).iter_no
        candidates = [r for r in results if r.iter_no == max_iter]
        best_result = next((r for r in candidates if r.mode == "LP"), candidates[-1])

        LOGGER.info(f" ├── Highest Iteration Detected: {max_iter}")
        LOGGER.info(f" └── Selected Result: {best_result.point} (Mode: {best_result.mode})")

        return best_result
