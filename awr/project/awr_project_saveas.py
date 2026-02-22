import os
from logger.logger import LOGGER


def save_project_as(app_instance: any, save_path: str) -> None:
    """
    Saves the active AWR project to the specified absolute file path.
    Verifies the operation by retrieving the newly assigned project name.
    """
    # AWR requires a strict absolute path to prevent saving to default directories
    absolute_save_path = os.path.abspath(save_path)

    LOGGER.info(f"├── Initiating project save operation to target path: {absolute_save_path}")

    try:
        project = app_instance.Project

        # Execute the SaveAs method with the absolute path
        project.SaveAs(absolute_save_path)

        active_project_name = project.Name
        LOGGER.info(f"└── Successfully saved active project as: {active_project_name}")

    except Exception as e:
        LOGGER.error(f"└── Failed to execute project save operation. Error details: {e}")