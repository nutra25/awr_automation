import os
from logger import LOGGER


def open_project(app_instance: any, project_path: str) -> bool:
    """
    Validates the existence of the target file and attempts to load it
    into the active AWR application instance.
    """
    LOGGER.info(f"├── Initiating project load operation from path: {project_path}")

    # Pre-flight check to ensure the target path exists on the file system
    if not os.path.exists(project_path):
        LOGGER.error(f"└── Aborting load operation. Specified project file does not exist: {project_path}")
        return False

    try:
        # Execute the Open method and capture the boolean result
        success = app_instance.Open(project_path)

        if success:
            # Verify success by retrieving the newly loaded active project name
            active_project_name = app_instance.Project.Name
            LOGGER.info(f"└── Successfully loaded the specified project file: {active_project_name}")
            return True
        else:
            LOGGER.error("└── Project open operation returned a failure status (False).")
            return False

    except Exception as e:
        LOGGER.error(f"└── Encountered a critical error during the project open operation: {e}")
        return False