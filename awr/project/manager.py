"""
manager.py (Project Domain)
Handles all API interactions related to project lifecycle, including
saving and loading empirical (.emp) files.
"""

from awr.project.open_project import open_project
from awr.project.awr_project_saveas import save_project_as

class ProjectManager:
    """
    Manages AWR Project level operations.
    """
    def __init__(self, app):
        self.app = app

    def save_current_project_as(self, save_path: str) -> None:
        """Saves the current active workspace to the specified absolute path."""
        save_project_as(self.app, save_path)

    def open_existing_project(self, project_path: str) -> bool:
        """Loads a predefined empirical project template into the workspace."""
        return open_project(self.app, project_path)