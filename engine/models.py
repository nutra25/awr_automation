"""
models.py
Defines the core domain data structures for the simulation engine.
Strictly adheres to the Pydantic BaseModel architecture for automated validation.
"""
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import List, Tuple, Any, Union, Optional
from enum import Enum, auto

from engine.utils import normalize_to_tuple

class StateType(Enum):
    ELEMENT = auto()
    RF_FREQUENCY = auto()

class Element(BaseModel):
    name: str = ""
    arg: str = ""

class State(BaseModel):
    name: str = ""
    value: Tuple[str, ...] = Field(default_factory=tuple, repr=False)
    element: Optional[List[Element]] = None
    type: Optional[StateType] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator('value', mode='before')
    @classmethod
    def _parse_value(cls, val: Any) -> Tuple[str, ...]:
        return normalize_to_tuple(val)

    @model_validator(mode='after')
    def _set_type_and_elements(self) -> 'State':
        if self.type is None:
            self.type = StateType.ELEMENT

        if self.type == StateType.ELEMENT:
            if self.element is None:
                self.element = []
        else:
            self.element = None

        return self

    def __repr__(self) -> str:
        el_str = f", element={self.element}" if self.element is not None else ""
        return f"State(name='{self.name}', type={self.type.name}, value={self.value}{el_str})"