"""
handlers.py
Manages the application of state variables to the simulation environment.
Delegates element and frequency configurations to the circuit manager based on structured configurations.
"""

from typing import Any
import objects
from logger.logger import LOGGER
from config import HandlersConfig


class StateHandler:
    """
    Handles state configurations and dispatches them to the appropriate driver interfaces.
    Now operates using the structured HandlersConfig object.
    """

    def __init__(self, circuit_manager: Any, config: HandlersConfig):
        """
        Initializes the state handler with the circuit manager and its configuration branch.
        """
        self.circuit = circuit_manager
        self.config = config

        self._state_handlers = {
            objects.StateType.ELEMENT: self._handle_element_state,
            objects.StateType.RF_FREQUENCY: self._handle_frequency_state,
        }

    def _handle_element_state(self, config_obj: Any, value: Any) -> None:
        """
        Updates schematic elements based on the state variable using the injected configuration.
        """
        LOGGER.debug(f"│   ├── Updating element state for {config_obj.name}: {value}")
        for elem in config_obj.element:
            self.circuit.configure_element(self.config.schematic_name, elem.name, {elem.arg: str(value)})

    def _handle_frequency_state(self, config_obj: Any, value: Any) -> None:
        """
        Updates the system frequency based on the state variable using the injected configuration.
        """
        LOGGER.debug(f"│   ├── Updating system frequency to: {value}")
        if isinstance(value, (list, tuple)):
            freq_val = [float(v) for v in value]
        else:
            freq_val = float(value)
        self.circuit.set_frequency(self.config.schematic_name, freq_val)

    def apply_configuration(self, config_obj: Any, value: Any) -> None:
        """
        Dispatches the configuration to the appropriate handler based on state type.
        """
        handler = self._state_handlers.get(config_obj.type)
        if handler:
            handler(config_obj, value)
        else:
            LOGGER.error(f"├── Unsupported StateType encountered: {config_obj.type}")


if __name__ == "__main__":
    import sys
    LOGGER.info("├── Starting standalone test sequence for handlers.py")
    try:
        class DummyCircuit:
            def configure_element(self, sch, el, params): pass
            def set_frequency(self, sch, freq): pass

        dummy_config = HandlersConfig(schematic_name="Test_Schematic")
        handler = StateHandler(DummyCircuit(), dummy_config)
        LOGGER.info("└── Test execution sequence completed successfully")
    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed: {ex}")
        sys.exit(1)