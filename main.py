"""
main.py
Application entry point.
Initializes the AWR driver and bootstraps the core simulation engine.
"""

from config import AWR_PATH, PROJECT_TEMPLATE_PATH
from logger.logger import LOGGER
from awr.awr_driver import AWRDriver
from engine.simulation_manager import SimulationManager


def main():
    try:
        selected_driver = AWRDriver(exe_path=AWR_PATH)

        LOGGER.info("├── Loading Project Template...")
        if not selected_driver.project.open_existing_project(PROJECT_TEMPLATE_PATH):
            LOGGER.critical("└── Failed to load project template. Aborting process.")
            return

        # Instantiate and start the core engine
        engine = SimulationManager(driver=selected_driver)
        engine.start()

    except KeyboardInterrupt:
        LOGGER.warning("└── Simulation interrupted by user intervention.")
    except Exception as e:
        LOGGER.critical(f"└── Unhandled Exception in Application Root: {e}")
        raise


if __name__ == "__main__":
    main()