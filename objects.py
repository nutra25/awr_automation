from dataclasses import dataclass, field
from typing import List, Tuple, Any, Union, Optional
import math
from decimal import Decimal
from enum import Enum, auto


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
class StateType(Enum):
    """Enumeration defining the state type: ELEMENT or RF_FREQUENCY."""
    ELEMENT = auto()
    RF_FREQUENCY = auto()

@dataclass
class Element:
    name: str = ""
    arg: str = ""

# --- State Class ---
@dataclass(init=False)
class State:
    """
    Represents a simulation state.
    Logic:
    - If 'element' is provided and 'type' is missing -> Auto-detects as ELEMENT.
    - If 'type' is RF_FREQUENCY -> Forces 'element' to be None.
    """
    name: str
    type: StateType
    element: Optional[List[Element]]
    _value: Tuple[str, ...] = field(repr=False)

    def __init__(
        self,
        name: str = "",
        value: Union[str, int, float, List[Any], Tuple[Any, ...]] = "",
        element: List["Element"] | None = None,
        type: StateType | None = None,  # Type is now optional
    ) -> None:
        self.name = name
        self._value = normalize_to_tuple(value)

        # LOGIC 1: Determine the StateType
        if type is not None:
            # Case A: User explicitly provided a type -> Use it.
            self.type = type
        else:
            # Case B: User did not provide a type -> Infer from 'element'.
            if element is not None:
                self.type = StateType.ELEMENT
            else:
                self.type = StateType.ELEMENT # Default fallback if nothing is provided

        # LOGIC 2: Configure the element list based on the determined type
        if self.type == StateType.ELEMENT:
            # If type is ELEMENT, ensure we have a list (empty if None provided)
            self.element = element if element is not None else []
        else:
            # If type is RF_FREQUENCY (or others), force element to None
            self.element = None

    @property
    def value(self) -> Tuple[str, ...]:
        """Public interface: always returns the canonical tuple representation."""
        return self._value

    @value.setter
    def value(self, val: Union[str, int, float, List[Any], Tuple[Any, ...]]) -> None:
        """Normalize any assignment into the canonical tuple form."""
        self._value = normalize_to_tuple(val)

    def __repr__(self):
        # Custom repr for cleaner output (hide element if None)
        el_str = f", element={self.element}" if self.element is not None else ""
        return f"State(name='{self.name}', type={self.type.name}, value={self.value}{el_str})"

@dataclass
class PullResult:
    iter_no: int
    mode: str # "SP" or "LP"
    point: str
    mag: str
    ang: str
# ============================================================

