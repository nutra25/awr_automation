import os
from core.logger import logger


def save_project_as(app_instance: any, save_path: str) -> None:
    """
    Saves the active AWR project to the specified absolute file path.
    Verifies the operation by retrieving the newly assigned project name.
    """
    # AWR requires a strict absolute path to prevent saving to default directories
    absolute_save_path = os.path.abspath(save_path)

    logger.info(f"├── Initiating project save operation to target path: {absolute_save_path}")

    try:
        project = app_instance.Project

        # Execute the SaveAs method with the absolute path
        project.SaveAs(absolute_save_path)

        active_project_name = project.Name
        logger.info(f"└── Successfully saved active project as: {active_project_name}")

    except Exception as e:
        logger.error(f"└── Failed to execute project save operation. Error details: {e}")