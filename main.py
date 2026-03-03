"""
main.py
Application entry point.
Initializes the AWR driver and bootstraps the core simulation engine using the hierarchical AppConfig.
"""

from core.config import app_config
from core.logger import logger
from awr.awr_driver import AWRDriver
from engine.simulation_manager import SimulationManager


def main():
    try:
        selected_driver = AWRDriver(exe_path=app_config.awr_path)

        logger.info("├── Loading Project Template...")
        # Note: Bypassing new project generation logic to operate strictly on the existing template.
        if not selected_driver.project.open_existing_project(app_config.project_template_path):
            logger.critical("└── Failed to load project template. Aborting process.")
            return

        # Pass the specific configuration branches to the core engine
        engine = SimulationManager(
            driver=selected_driver,
            engine_config=app_config.engine,
            rf_design_config=app_config.rf_design
        )
        engine.start()

    except KeyboardInterrupt:
        logger.warning("└── Simulation interrupted by user intervention.")
    except Exception as e:
        logger.critical(f"└── Unhandled Exception in Application Root: {e}")
        raise


if __name__ == "__main__":
    main()