import os
from core.logger import logger


def open_project(app_instance: any, project_path: str) -> bool:
    """
    Validates the existence of the target file and attempts to load it
    into the active AWR application instance.
    """
    logger.info(f"├── Initiating project load operation from path: {project_path}")

    # Pre-flight check to ensure the target path exists on the file system
    if not os.path.exists(project_path):
        logger.error(f"└── Aborting load operation. Specified project file does not exist: {project_path}")
        return False

    try:
        # Execute the Open method and capture the boolean result
        success = app_instance.Open(project_path)

        if success:
            # Verify success by retrieving the newly loaded active project name
            active_project_name = app_instance.Project.Name
            logger.info(f"└── Successfully loaded the specified project file: {active_project_name}")
            return True
        else:
            logger.error("└── Project open operation returned a failure status (False).")
            return False

    except Exception as e:
        logger.error(f"└── Encountered a critical error during the project open operation: {e}")
        return False