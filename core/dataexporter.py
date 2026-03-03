"""
dataexporter.py
A highly decoupled, comprehensive data export module capable of saving
various data formats (CSV, JSON, HTML, Binary/Images) to persistent storage.
Utilizes an embedded configuration class for self-contained dependency injection.
Strictly adheres to the tree-branch logging structure.
"""

import csv
import os
import json
from dataclasses import dataclass
from typing import List, Dict, Any

from core.logger import LOGGER


@dataclass
class DataExporterConfig:
    """
    Configuration node for the DataExporter module.
    """
    base_directory: str


class DataExporter:
    """
    Manages generic data persistence across multiple formats within a specified
    base directory, operating via a self-contained configuration object.
    """

    def __init__(self, config: DataExporterConfig):
        """
        Initializes the exporter with its specific configuration branch.
        """
        self.config = config
        self._ensure_directory(self.config.base_directory)

    def _ensure_directory(self, path: str) -> None:
        """
        Ensures the target directory exists before attempting file operations.
        """
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            LOGGER.debug(f"├── Created target directory: {path}")

    def _get_filepath(self, filename: str) -> str:
        """
        Constructs and returns the absolute file path for a given filename.
        """
        return os.path.join(self.config.base_directory, filename)

    def initialize_csv(self, filename: str, headers: List[str]) -> bool:
        """
        Creates a new CSV file and writes the header row.
        """
        filepath = self._get_filepath(filename)
        LOGGER.info(f"├── Initializing CSV storage file at: {filepath}")
        try:
            with open(filepath, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(headers)
            LOGGER.info(f"└── Successfully generated headers for {filename}.")
            return True
        except IOError as e:
            LOGGER.error(f"└── Failed to initialize CSV file {filename}. Critical error: {e}")
            return False

    def append_csv_row(self, filename: str, row_data: List[Any]) -> None:
        """
        Appends a single row of arbitrary data to the specified CSV file.
        """
        filepath = self._get_filepath(filename)
        try:
            with open(filepath, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(row_data)
        except IOError as e:
            LOGGER.error(f"├── Write operation failed for {filename}. Target row dropped.")
            LOGGER.error(f"└── Error details: {e}")

    def save_json(self, filename: str, data: Dict[str, Any]) -> bool:
        """
        Serializes a dictionary to a JSON file format.
        """
        filepath = self._get_filepath(filename)
        LOGGER.info(f"├── Commencing JSON serialization to: {filepath}")
        try:
            with open(filepath, mode='w', encoding='utf-8') as file:
                json.dump(data, file, indent=4)
            LOGGER.info(f"└── JSON export sequence completed successfully for {filename}.")
            return True
        except (IOError, TypeError) as e:
            LOGGER.error(f"└── Failed to execute JSON export. Error details: {e}")
            return False

    def save_text(self, filename: str, content: str) -> bool:
        """
        Saves raw string content to a text-based file (e.g., HTML, TXT, XML).
        """
        filepath = self._get_filepath(filename)
        LOGGER.info(f"├── Saving text-based content to: {filepath}")
        try:
            with open(filepath, mode='w', encoding='utf-8') as file:
                file.write(content)
            LOGGER.info(f"└── Text export sequence completed successfully for {filename}.")
            return True
        except IOError as e:
            LOGGER.error(f"└── Failed to save text file {filename}. Error details: {e}")
            return False

    def save_binary(self, filename: str, data: bytes) -> bool:
        """
        Saves raw byte data to a binary file (e.g., PNG, JPG, PDF, SVG).
        """
        filepath = self._get_filepath(filename)
        LOGGER.info(f"├── Saving binary content to: {filepath}")
        try:
            with open(filepath, mode='wb') as file:
                file.write(data)
            LOGGER.info(f"└── Binary export sequence completed successfully for {filename}.")
            return True
        except IOError as e:
            LOGGER.error(f"└── Failed to save binary file {filename}. Error details: {e}")
            return False

    def resolve_external_path(self, filename: str) -> str:
        """
        Returns the absolute path for external tools to save files directly,
        while tracking the action in the logs.
        """
        filepath = os.path.abspath(self._get_filepath(filename))
        LOGGER.debug(f"├── Resolved external export path: {filepath}")
        return filepath


if __name__ == "__main__":
    import sys
    LOGGER.info("├── Starting standalone test sequence for dataexporter.py")
    try:
        test_config = DataExporterConfig(base_directory="./test_export_dir")
        exporter = DataExporter(config=test_config)
        LOGGER.info(f"│   ├── Exporter configured with base directory: {exporter.config.base_directory}")
        LOGGER.info("└── Test execution sequence completed successfully")
    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed: {ex}")
        sys.exit(1)