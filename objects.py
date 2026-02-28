"""
objects.py
Defines the core domain data structures and utility functions.
These elements represent pure data contracts and thus do not require configuration injection.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Any, Union, Optional
import math
from decimal import Decimal
from enum import Enum, auto


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def normalize_to_tuple(x: Any) -> Tuple[str, ...]:
    """
    Converts the provided input into a uniform tuple of strings.
    """
    if isinstance(x, (list, tuple)):
        return tuple(str(v) for v in x)
    return (str(x),)


def _auto_decimals(*nums: float) -> int:
    """
    Determines the maximum number of decimal places required to represent
    the provided floating-point numbers accurately without precision loss.
    """

    def dec_places(x: float) -> int:
        d = Decimal(str(x)).normalize()
        exp = d.as_tuple().exponent
        return max(0, -exp)

    return max(dec_places(n) for n in nums)


def generate_sweep_values(
        start: float,
        stop: float,
        step: float,
        decimals: Optional[int] = None
) -> Tuple[str, ...]:
    """
    Generates a sequence of formatted string values from start to stop
    utilizing a floating-point step metric. Ensures explicit inclusion
    of boundary parameters.
    """
    if step == 0:
        raise ValueError("Sweep step magnitude cannot be zero.")

    if decimals is None:
        decimals = _auto_decimals(start, stop, step)

    if start < stop and step < 0:
        step = abs(step)
    elif start > stop and step > 0:
        step = -abs(step)

    count = int(math.floor((stop - start) / step))
    values = [f"{(start + i * step):.{decimals}f}" for i in range(abs(count) + 1)]

    if values[-1] != f"{stop:.{decimals}f}":
        values.append(f"{stop:.{decimals}f}")

    return tuple(values)


# ============================================================
# DOMAIN DATA STRUCTURES
# ============================================================

class StateType(Enum):
    """Enumeration identifying the nature of the state variable."""
    ELEMENT = auto()
    RF_FREQUENCY = auto()


@dataclass
class Element:
    """Represents a discrete component configuration targeting the simulator."""
    name: str = ""
    arg: str = ""


@dataclass(init=False)
class State:
    """
    Encapsulates the simulation state parameters.
    Implements intelligent type inference based on provided instantiation arguments.
    """
    name: str
    type: StateType
    element: Optional[List[Element]]
    _value: Tuple[str, ...] = field(repr=False)

    def __init__(
            self,
            name: str = "",
            value: Union[str, int, float, List[Any], Tuple[Any, ...]] = "",
            element: Optional[List["Element"]] = None,
            type: Optional[StateType] = None,
    ) -> None:
        self.name = name
        self._value = normalize_to_tuple(value)

        # Type determination protocol
        if type is not None:
            self.type = type
        else:
            self.type = StateType.ELEMENT if element is not None else StateType.ELEMENT

        # Element validation protocol
        if self.type == StateType.ELEMENT:
            self.element = element if element is not None else []
        else:
            self.element = None

    @property
    def value(self) -> Tuple[str, ...]:
        """Exposes the canonical tuple representation of the state value."""
        return self._value

    @value.setter
    def value(self, val: Union[str, int, float, List[Any], Tuple[Any, ...]]) -> None:
        """Enforces normalization upon state value reassignment."""
        self._value = normalize_to_tuple(val)

    def __repr__(self) -> str:
        el_str = f", element={self.element}" if self.element is not None else ""
        return f"State(name='{self.name}', type={self.type.name}, value={self.value}{el_str})"


@dataclass
class PullResult:
    """Records the absolute metrics extracted from a specific load/source pull iteration."""
    iter_no: int
    mode: str  # "SP" (Source Pull) or "LP" (Load Pull)
    point: str
    mag: float
    ang: float


if __name__ == "__main__":
    import sys

    print("├── Starting standalone test sequence for objects.py")
    try:
        test_state = State(name="Test_Freq", value=5.0, type=StateType.RF_FREQUENCY)
        print(f"│   ├── Validated State Initialization: {test_state}")

        sweep = generate_sweep_values(1.0, 2.0, 0.5)
        print(f"│   ├── Generated Sweep Values: {sweep}")

        print("└── Test execution sequence completed successfully")
    except Exception as ex:
        print(f"└── Test execution failed: {ex}")
        sys.exit(1)