"""
manager.py (Project Domain)
Handles all API interactions related to project lifecycle, including
saving and loading empirical (.emp) files.
"""

import sys
from typing import Any, Dict, Optional

from awr.project.open_project import open_project
from awr.project.project_saveas import save_project_as
from awr.project.new_project_with_library import new_project_with_library


class ProjectManager:
    """
    Manages AWR Project level operations.
    """
    def __init__(self, app):
        self.app = app

    def new_project_with_library(self, library_name: str, library_version: Optional[str] = None) -> bool:
        """Initializes a new project with the specified process library."""
        return new_project_with_library(self.app, library_name, library_version)

    def save_current_project_as(self, save_path: str) -> None:
        """Saves the current active workspace to the specified absolute path."""
        save_project_as(self.app, save_path)

    def open_existing_project(self, project_path: str) -> bool:
        """Loads a predefined empirical project template into the workspace."""
        return open_project(self.app, project_path)