"""
handlers.py
Manages the application of state variables to the simulation environment.
Delegates element and frequency configurations to the circuit manager based on structured configurations.
Strictly adheres to the tree-branch logging hierarchy.
"""

from typing import Any
from dataclasses import dataclass
from logger.logger import LOGGER


@dataclass
class HandlersConfig:
    """Configuration node for state variable handlers."""
    schematic_name: str = "Load_Pull_Template"


class StateHandler:
    """
    Handles state configurations and dispatches them to the appropriate driver interfaces.
    """

    def __init__(self, circuit_manager: Any, config: HandlersConfig):
        self.circuit = circuit_manager
        self.config = config

        self._state_handlers = {
            objects.StateType.ELEMENT: self._handle_element_state,
            objects.StateType.RF_FREQUENCY: self._handle_frequency_state,
        }

    def _handle_element_state(self, config_obj: Any, value: Any) -> None:
        LOGGER.debug(f"│   ├── Updating element state for {config_obj.name}: {value}")
        for elem in config_obj.element:
            self.circuit.configure_element(self.config.schematic_name, elem.name, {elem.arg: str(value)})

    def _handle_frequency_state(self, config_obj: Any, value: Any) -> None:
        LOGGER.debug(f"│   ├── Updating system frequency to: {value}")
        if isinstance(value, (list, tuple)):
            freq_val = [float(v) for v in value]
        else:
            freq_val = float(value)
        self.circuit.set_frequency(self.config.schematic_name, freq_val)

    def apply_configuration(self, config_obj: Any, value: Any) -> None:
        handler = self._state_handlers.get(config_obj.type)
        if handler:
            handler(config_obj, value)
        else:
            LOGGER.error(f"├── Unsupported StateType encountered: {config_obj.type}")