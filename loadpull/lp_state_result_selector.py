from abc import ABC, abstractmethod
from typing import List
from logger.logger import LOGGER
import objects


class BestResultStrategy(ABC):
    """
    Abstract base class (Interface) for result selection strategies.
    Defines the contract for selecting the 'best' result from a list of simulation outcomes.
    """

    @abstractmethod
    def find_best(self, results: List['objects.PullResult']) -> 'objects.PullResult':
        """
        Selects and returns the optimal PullResult based on the concrete strategy.
        """
        pass


class MaxPointStrategy(BestResultStrategy):
    """
    Classic Method: Selects the result with the highest 'point' value.
    typically used for maximizing Output Power (dBm) or PAE (%).
    """

    def find_best(self, results: List['objects.PullResult']) -> 'objects.PullResult':
        LOGGER.info("Executing Strategy: MaxPointStrategy")

        if not results:
            LOGGER.error(" └── Result list is empty; cannot determine the best result.")
            raise ValueError("Result list is empty.")

        # Identify the result with the maximum numerical value in the 'point' field
        best_result = max(results, key=lambda x: float(x.point))

        LOGGER.info(f" ├── Criteria: Highest value found.")
        LOGGER.info(
            f" └── Selected Result: {best_result.point} (Iter: {best_result.iter_no}, Mode: {best_result.mode})")

        return best_result


class TargetPointStrategy(BestResultStrategy):
    """
    Alternative Method: Selects the result closest to a specific target value.
    Ideal for finding specific compression points (e.g., closest to 40dBm).
    """

    def __init__(self, target_value: float):
        self.target = target_value

    def find_best(self, results: List['objects.PullResult']) -> 'objects.PullResult':
        LOGGER.info(f"Executing Strategy: TargetPointStrategy (Target: {self.target})")

        if not results:
            LOGGER.error(" └── Result list is empty; cannot determine the best result.")
            raise ValueError("Result list is empty.")

        # Find the result with the minimum absolute difference from the target
        best_result = min(results, key=lambda x: abs(float(x.point) - self.target))

        diff = abs(float(best_result.point) - self.target)
        LOGGER.info(f" ├── Closest match found (Difference: {diff:.4f}).")
        LOGGER.info(f" └── Selected Result: {best_result.point} (Iter: {best_result.iter_no})")

        return best_result


class LastIterationStrategy(BestResultStrategy):
    """
    Iteration Priority Method: Always selects the result from the final iteration.
    Useful when the simulation converges iteratively and the last step represents
    the most refined state, regardless of the metric magnitude.
    """

    def find_best(self, results: List['objects.PullResult']) -> 'objects.PullResult':
        LOGGER.info("Executing Strategy: LastIterationStrategy")

        if not results:
            LOGGER.error(" └── Result list is empty; cannot determine the best result.")
            raise ValueError("Result list is empty.")

        # 1. Determine the highest iteration number available in the results
        max_iter = max(results, key=lambda x: x.iter_no).iter_no

        # 2. Filter results belonging to this last iteration
        candidates = [r for r in results if r.iter_no == max_iter]

        # 3. If multiple modes exist (SP and LP), prefer Load Pull (LP) as the final state.
        #    If LP is not found, take the last appended item in the list.
        best_result = next((r for r in candidates if r.mode == "LP"), candidates[-1])

        LOGGER.info(f" ├── Highest Iteration Detected: {max_iter}")
        LOGGER.info(f" └── Selected Result: {best_result.point} (Mode: {best_result.mode})")

        return best_result