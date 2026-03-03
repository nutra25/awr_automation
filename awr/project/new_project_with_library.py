"""
new_project_with_library.py
Provides atomic functionality to initialize a new AWR project utilizing a specific process library.
Supports both standard and version-specific library initialization methods.
Strictly adheres to the tree-branch logging hierarchy.
"""

import pyawr.mwoffice as mwoffice
import sys
from typing import Any, Optional

from core.logger import LOGGER


def new_project_with_library(app: Any, library_name: str, library_version: Optional[str] = None) -> bool:
    """
    Creates a new AWR project initialized with a specified process library.

    Args:
        app: The active AWR MWOffice COM application instance.
        library_name (str): The exact name of the process library to be loaded.
        library_version (Optional[str]): The specific version of the library. If provided,
                                         it utilizes the extended (Ex) API method.

    Returns:
        bool: True if the project was successfully created, False otherwise.
    """
    LOGGER.info(f"├── Initiating new project creation with library '{library_name}'...")

    try:
        if library_version:
            LOGGER.debug(f"│   ├── Target version specified: {library_version}")
            # Method 2: Initialize with a specific library version
            app.NewWithProcessLibraryEx(library_name, library_version)
        else:
            LOGGER.debug("│   ├── No specific version provided. Using default library loader.")
            # Method 1: Initialize using only the library name
            app.NewWithProcessLibrary(library_name)

        LOGGER.info("└── Successfully generated new project with the specified process library.")
        return True

    except Exception as e:
        LOGGER.error(f"└── Failed to create new project with library '{library_name}'. Details: {e}")
        return False


# Standalone Test Execution Block
if __name__ == "__main__":
    LOGGER.info("Starting standalone test sequence for new_project_with_library.py module.")

    try:
        # Attempt to establish a connection with an active AWR instance
        test_app = mwoffice.CMWOffice()
        LOGGER.info("├── Successfully connected to AWR Microwave Office for testing.")

        # Test Parameters
        test_lib_name = "MA_RFP"

        # Test Case 1: Standard initialization
        LOGGER.info("├── Executing Test Case 1: Standard Initialization")
        result_1 = new_project_with_library(test_app, test_lib_name)

        # Test Case 2: Version-specific initialization (Optional, assuming version "1.0" exists)
        # LOGGER.info("├── Executing Test Case 2: Version-Specific Initialization")
        # result_2 = new_project_with_library(test_app, test_lib_name, library_version="1.0")

        if result_1:
            LOGGER.info("└── Test execution sequence completed successfully.")
        else:
            LOGGER.warning("└── Test execution completed, but project creation failed.")

    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed. Ensure AWR application is running. Details: {ex}")
        sys.exit(1)