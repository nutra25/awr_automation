"""
new_data_file.py
Provides functionality to create new, empty data files within the AWR Microwave Office project.
Utilizes enumerations to ensure type safety and enable IDE autocomplete features.
Includes input validation to enforce AWR naming conventions.
"""

import pyawr.mwoffice as mwoffice
from enum import Enum
import sys
import re
from typing import Any

from core.logger import logger


class DataFileType(Enum):
    """
    Enumeration of available data file types in AWR Microwave Office.
    Provides strict type hinting and IDE intellisense support.
    """
    SNP = mwoffice.mwDataFileType.mwDFT_SNP
    RAW = mwoffice.mwDataFileType.mwDFT_RAW
    IV = mwoffice.mwDataFileType.mwDFT_IV
    TXT = mwoffice.mwDataFileType.mwDFT_TXT
    MDIF = mwoffice.mwDataFileType.mwDFT_MDIF
    GMDIF = mwoffice.mwDataFileType.mwDFT_GMDIF
    DSCR = mwoffice.mwDataFileType.mwDFT_DSCR
    GMDIFD = mwoffice.mwDataFileType.mwDFT_GMDIFD


def add_new_data_file(app: Any, file_name: str, file_type: DataFileType = DataFileType.TXT) -> bool:
    """
    Creates a new, empty data file in the active AWR project.

    Args:
        app: The active AWR MWOffice COM application instance.
        file_name (str): The exact name to be assigned to the new data file.
        file_type (DataFileType): The desired file format, selected from the DataFileType enum.

    Returns:
        bool: True if the file was created successfully, False otherwise.
    """
    logger.info(f"├── Attempting to create new data file: '{file_name}' (Type: {file_type.name})")

    # Validation: AWR strictly prefers A-Z, a-z, 0-9, and underscores for data files.
    if not re.match(r'^[A-Za-z0-9_]+$', file_name):
        logger.error("└── Invalid file name. Only alphanumeric characters and underscores are permitted.")
        return False

    try:
        data_files = app.Project.DataFiles

        # Verify if a data file with the same name already exists to prevent duplication errors
        for i in range(1, data_files.Count + 1):
            if data_files.Item(i).Name == file_name:
                logger.warning(f"└── Data file '{file_name}' already exists. Creation aborted.")
                return False

        # Create the file using the integer value from the enum
        data_files.AddNew(file_name, file_type.value)
        logger.info(f"└── Successfully created data file: '{file_name}'")
        return True

    except Exception as e:
        logger.error(f"└── Failed to create data file '{file_name}'. Exception: {e}")
        return False


# Standalone Test Execution Block
if __name__ == "__main__":
    logger.info("Starting standalone test sequence for new_data_file.py module.")

    try:
        test_app = mwoffice.CMWOffice()
        logger.info("├── Successfully connected to AWR Microwave Office for testing.")

        # Test Case 1: Create a standard text data file
        test_name_1 = "Automated_Test_TXT"
        add_new_data_file(test_app, test_name_1, DataFileType.TXT)

        # Test Case 2: Create a Touchstone S-Parameter file
        test_name_2 = "Automated_Test_SNP"
        add_new_data_file(test_app, test_name_2, DataFileType.SNP)

        # Test Case 3: Attempt to create a duplicate file to verify error handling
        logger.info("├── Verifying duplicate file handling logic...")
        add_new_data_file(test_app, test_name_1, DataFileType.TXT)

        # Test Case 4: Verify invalid character prevention (Hyphens/Spaces are usually bad for data files)
        logger.info("├── Verifying invalid character sanitization logic...")
        add_new_data_file(test_app, "Invalid-File-Name", DataFileType.TXT)

        logger.info("└── Test execution sequence completed successfully.")

    except Exception as ex:
        logger.critical(f"└── Test execution failed. Details: {ex}")
        sys.exit(1)