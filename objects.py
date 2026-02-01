from dataclasses import dataclass, field
from typing import List, Tuple, Any, Union, Optional
import math
from decimal import Decimal


# ============================================================
# HELPER FUNCTIONS FOR OBJECTS.PY
def normalize_to_tuple(x) -> Tuple[str, ...]:
    """
    Converts the given input into a tuple of strings.
    Examples:
        "13" -> ("13",)
        ("13", "14") -> ("13", "14")
    """
    if isinstance(x, (list, tuple)):
        return tuple(str(v) for v in x)
    return (str(x),)

def _auto_decimals(*nums: float) -> int:
    def dec_places(x: float) -> int:
        # Convert through Decimal to avoid float representation noise.
        d = Decimal(str(x)).normalize()
        # If it's an integer, exponent >= 0
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
    Generates values from start to stop using a float step.
    Always includes both start and stop (as formatted strings).
    If decimals is None, it is inferred from start/stop/step.
    """
    if step == 0:
        raise ValueError("step cannot be zero")

    if decimals is None:
        decimals = _auto_decimals(start, stop, step)

    # Fix step direction if needed
    if start < stop and step < 0:
        step = abs(step)
    elif start > stop and step > 0:
        step = -abs(step)

    # Number of steps (inclusive), using floor for stability
    count = int(math.floor((stop - start) / step))
    values = [f"{(start + i * step):.{decimals}f}" for i in range(abs(count) + 1)]

    # Ensure stop is included (after formatting)
    if values[-1] != f"{stop:.{decimals}f}":
        values.append(f"{stop:.{decimals}f}")

    return tuple(values)
# ============================================================


# ============================================================
# DATA CLASSES
@dataclass
class Element:
    name: str = ""
    arg: str = ""

@dataclass(init=False)
class State:
    name: str = ""
    element: List["Element"] = field(default_factory=list)
    # Internal canonical representation (always a tuple of strings).
    _value: Tuple[str, ...] = field(default_factory=tuple, repr=False)

    def __init__(
        self,
        name: str = "",
        value: Union[str, int, float, List[Any], Tuple[Any, ...]] = "",
        element: List["Element"] | None = None,
    ) -> None:
        self.name = name
        self.element = element if element is not None else []
        self._value = normalize_to_tuple(value)

    @property
    def value(self) -> Tuple[str, ...]:
        # Public interface: always return the canonical tuple representation.
        return self._value

    @value.setter
    def value(self, val: Union[str, int, float, List[Any], Tuple[Any, ...]]) -> None:
        # Normalize any assignment into the canonical tuple form.
        self._value = normalize_to_tuple(val)

@dataclass
class PullResult:
    iter_no: int
    mode: str # "SP" or "LP"
    point: str
    mag: str
    ang: str
# ============================================================

