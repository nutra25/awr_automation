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
from rfdesign.loadpull.create_new_loadpull_project import create_loadpull_project

def main():
    try:
        selected_driver = AWRDriver(exe_path=app_config.awr_path)

        exporter_config = DataExporterConfig(base_directory=app_config.engine.run_dir)
        exporter = DataExporter(config=exporter_config)

        context = AutomationContext(
            driver=selected_driver,
            exporter=exporter,
            config=app_config
        )

        logger.info("├── Creating New Load-Pull Project Environment...")

        project_created = create_loadpull_project(context)

        if not project_created:
            logger.critical("└── Failed to create new load-pull project. Aborting process.")
            return

        logger.info("├── Initializing Simulation Engine...")
        engine = SimulationManager(context=context)
        engine.start()

        engine = SimulationManager(context=context)
        engine.start()

    except KeyboardInterrupt:
        logger.warning("└── Simulation interrupted by user intervention.")
    except Exception as e:
        logger.critical(f"└── Unhandled Exception in Application Root: {e}")
        raise


if __name__ == "__main__":
    main()