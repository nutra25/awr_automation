"""
models.py
Defines the core domain data structures for the simulation engine.
Strictly adheres to the dataclass driven architecture.
"""
from dataclasses import dataclass, field
from typing import List, Tuple, Any, Union, Optional
from enum import Enum, auto

# Import the utility function from its proper module
from engine.utils import normalize_to_tuple


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
    """Encapsulates the simulation state parameters."""
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

        if type is not None:
            self.type = type
        else:
            self.type = StateType.ELEMENT if element is not None else StateType.ELEMENT

        if self.type == StateType.ELEMENT:
            self.element = element if element is not None else []
        else:
            self.element = None

    @property
    def value(self) -> Tuple[str, ...]:
        return self._value

    @value.setter
    def value(self, val: Union[str, int, float, List[Any], Tuple[Any, ...]]) -> None:
        self._value = normalize_to_tuple(val)

    def __repr__(self) -> str:
        el_str = f", element={self.element}" if self.element is not None else ""
        return f"State(name='{self.name}', type={self.type.name}, value={self.value}{el_str})"