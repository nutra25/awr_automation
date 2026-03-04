"""
main.py
Application entry point.
Implements a 2-phase architecture:
1. Generation Phase: Launches AWR, creates the project from scratch, saves, and cleanly exits.
2. Simulation Phase: Relaunches AWR, opens the fresh project, and executes the simulation engine.
"""

import time
import os
from core.config import app_config
from core.logger import logger
from awr.awr_driver import AWRDriver
from engine.simulation_manager import SimulationManager
from core.dataexporter import DataExporter, DataExporterConfig
from core.context import AutomationContext
from rfdesign.loadpull.create_new_loadpull_project import create_loadpull_project


def close_awr_safely(driver):
    """
    Forcefully closes the AWR application via system kill to ensure a clean state.
    Since the project is already explicitly saved, a graceful COM quit is bypassed
    to prevent zombie processes and save execution time.
    """
    logger.info("│   ├── Terminating AWR application directly via system command...")
    try:
        os.system("taskkill /f /im MWOffice.exe >nul 2>&1")

        time.sleep(3)
    except Exception as e:
        logger.error(f"│   └── Failed to execute system kill command: {e}")


def main():
    try:
        # =========================================================================
        # PHASE 1: PROJECT GENERATION & PREPARATION
        # =========================================================================
        logger.info("==================================================")
        logger.info(" PHASE 1: PROJECT GENERATION")
        logger.info("==================================================")

        creation_driver = AWRDriver(exe_path=app_config.awr_path)
        exporter_config = DataExporterConfig(base_directory=app_config.engine.run_dir)
        exporter = DataExporter(config=exporter_config)

        creation_context = AutomationContext(
            driver=creation_driver,
            exporter=exporter,
            config=app_config
        )

        logger.info("├── Triggering Load-Pull Project Creation Macro...")
        success = create_loadpull_project(context=creation_context)

        if not success:
            logger.critical("└── Project generation failed. Aborting full sequence.")
            return

        saved_project_path = app_config.rf_design.project_generation.save_path
        logger.info(f"├── Project successfully generated and saved to: {saved_project_path}")

        logger.info("├── Closing AWR Application to clear cache and memory...")
        close_awr_safely(creation_driver)
        logger.info("└── Phase 1 Completed.\n")


        # =========================================================================
        # PHASE 2: SIMULATION EXECUTION
        # =========================================================================
        logger.info("==================================================")
        logger.info(" PHASE 2: SIMULATION EXECUTION")
        logger.info("==================================================")

        logger.info("├── Relaunching AWR Application for simulation...")
        sim_driver = AWRDriver(exe_path=app_config.awr_path)

        sim_context = AutomationContext(
            driver=sim_driver,
            exporter=exporter,
            config=app_config
        )

        logger.info(f"├── Loading Generated Project from: {saved_project_path}")
        if not sim_driver.project.open_existing_project(saved_project_path):
            logger.critical("└── Failed to load the freshly generated project. Aborting process.")
            return

        logger.info("├── Starting Core Simulation Engine...")
        engine = SimulationManager(context=sim_context)
        engine.start()

    except KeyboardInterrupt:
        logger.warning("└── Simulation interrupted by user intervention.")
    except Exception as e:
        logger.critical(f"└── Unhandled Exception in Application Root: {e}")
        raise


if __name__ == "__main__":
    main()