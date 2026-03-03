"""
main.py
Application entry point.
Initializes the AWR driver and bootstraps the core simulation engine using Context architecture.
"""

from core.config import app_config
from core.logger import logger
from awr.awr_driver import AWRDriver
from engine.simulation_manager import SimulationManager
from core.dataexporter import DataExporter, DataExporterConfig
from core.context import AutomationContext


def main():
    try:
        selected_driver = AWRDriver(exe_path=app_config.awr_path)

        exporter_config = DataExporterConfig(base_directory=app_config.engine.run_dir)
        exporter = DataExporter(config=exporter_config)

        logger.info("├── Loading Project Template...")

        if not selected_driver.project.open_existing_project(app_config.project_template_path):
            logger.critical("└── Failed to load project template. Aborting process.")
            return

        context = AutomationContext(
            driver=selected_driver,
            exporter=exporter,
            config=app_config
        )

        engine = SimulationManager(context=context)
        engine.start()

    except KeyboardInterrupt:
        logger.warning("└── Simulation interrupted by user intervention.")
    except Exception as e:
        logger.critical(f"└── Unhandled Exception in Application Root: {e}")
        raise


if __name__ == "__main__":
    main()