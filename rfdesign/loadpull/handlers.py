"""
handlers.py
Manages the application of state variables to the simulation environment.
Delegates element and frequency configurations to the circuit manager.
"""

from typing import Any
import objects
from logger.logger import LOGGER


class StateHandler:
    """
    Handles state configurations and dispatches them to the appropriate driver interfaces.
    Operates independently of global configurations via dependency injection.
    """

    def __init__(self, circuit_manager: Any, schematic_name: str):
        """
        Initializes the state handler with the necessary circuit manager instance and schematic context.
        """
        self.circuit = circuit_manager
        self.schematic_name = schematic_name

        self._state_handlers = {
            objects.StateType.ELEMENT: self._handle_element_state,
            objects.StateType.RF_FREQUENCY: self._handle_frequency_state,
        }

    def _handle_element_state(self, config_obj: Any, value: Any) -> None:
        """
        Updates schematic elements based on the state variable by injecting context.
        """
        LOGGER.debug(f"│   ├── Updating element state for {config_obj.name}: {value}")
        for elem in config_obj.element:
            self.circuit.configure_element(self.schematic_name, elem.name, {elem.arg: str(value)})

    def _handle_frequency_state(self, config_obj: Any, value: Any) -> None:
        """
        Updates the system frequency based on the state variable by injecting context.
        """
        LOGGER.debug(f"│   ├── Updating system frequency to: {value}")
        if isinstance(value, (list, tuple)):
            freq_val = [float(v) for v in value]
        else:
            freq_val = float(value)
        self.circuit.set_frequency(self.schematic_name, freq_val)

    def apply_configuration(self, config_obj: Any, value: Any) -> None:
        """
        Dispatches the configuration to the appropriate handler based on state type.
        """
        handler = self._state_handlers.get(config_obj.type)
        if handler:
            handler(config_obj, value)
        else:
            LOGGER.error(f"├── Unsupported StateType encountered: {config_obj.type}")