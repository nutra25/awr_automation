import re
from enum import Enum
from pyawr import mwoffice

from awr.awr_component import AWRComponent

class DataFileType(Enum):
    SNP = mwoffice.mwDataFileType.mwDFT_SNP
    RAW = mwoffice.mwDataFileType.mwDFT_RAW
    IV = mwoffice.mwDataFileType.mwDFT_IV
    TXT = mwoffice.mwDataFileType.mwDFT_TXT
    MDIF = mwoffice.mwDataFileType.mwDFT_MDIF
    GMDIF = mwoffice.mwDataFileType.mwDFT_GMDIF
    DSCR = mwoffice.mwDataFileType.mwDFT_DSCR
    GMDIFD = mwoffice.mwDataFileType.mwDFT_GMDIFD

class DataFile(AWRComponent):

    def add_new_data_file(self, file_name: str, file_type: DataFileType) -> bool:

        self.logger.info(f"├── Attempting to create new data file: '{file_name}' (Type: {file_type.name})")

        if not re.match(r'^[A-Za-z0-9_]+$', file_name):
            self.logger.error("└── Invalid file name. Only alphanumeric characters and underscores are permitted.")
            return False

        try:
            data_files = self.app.Project.DataFiles
            if data_files.Exists(file_name):
                self.logger.warning(f"└── Data file '{file_name}' already exists. Creation aborted.")
                return False

            data_files.AddNew(file_name, file_type.value)
            self.logger.info(f"└── Successfully created data file: '{file_name}'")
            return True

        except Exception as e:
            self.logger.error(f"└── Failed to create data file '{file_name}'. Exception: {e}")
            return False