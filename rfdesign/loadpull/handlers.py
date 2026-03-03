
"""
handlers.py
Manages the application of state variables to the simulation environment.
Delegates element and frequency configurations to the circuit manager based on context.
Strictly adheres to the tree-branch logging hierarchy.
"""

from typing import Any
from dataclasses import dataclass
from engine.models import StateType
from core.logger import logger


@dataclass
class HandlersConfig:
    """Configuration node for state variable handlers."""
    schematic_name: str = "Load_Pull_Template"


class StateHandler:
    """
    Handles state configurations and dispatches them to the appropriate driver interfaces.
    Operates strictly via the injected AutomationContext.
    """

    def __init__(self, context: Any):
        self.context = context

        self.circuit = self.context.driver.circuit
        self.config = self.context.config.rf_design.loadpull.handlers

        self._state_handlers = {
            StateType.ELEMENT: self._handle_element_state,
            StateType.RF_FREQUENCY: self._handle_frequency_state,
        }

    def _handle_element_state(self, config_obj: Any, value: Any) -> None:
        logger.debug(f"│   ├── Updating element state for {config_obj.name}: {value}")
        for elem in config_obj.element:
            self.circuit.configure_element(self.config.schematic_name, elem.name, {elem.arg: str(value)})

    def _handle_frequency_state(self, config_obj: Any, value: Any) -> None:
        logger.debug(f"│   ├── Updating system frequency to: {value}")
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
            logger.error(f"├── Unsupported StateType encountered: {config_obj.type}")