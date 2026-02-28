"""
manager.py (Data File Domain)
Handles all API interactions related to data files within the AWR project.
Enforces domain encapsulation.
"""

from typing import Any
from awr.data_file.new_data_file import add_new_data_file, DataFileType

class DataFileManager:
    """
    Manages AWR Data File operations (creation, importing, linking).
    """
    def __init__(self, app: Any):
        self.app = app

    def add_new(self, file_name: str, file_type: DataFileType) -> bool:
        """
        Creates a new, empty data file in the project.
        Requires a DataFileType enum for type safety.
        """
        return add_new_data_file(self.app, file_name, file_type)