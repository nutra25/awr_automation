"""
paths.py
Defines fundamental directory structures and dynamic paths for the project.
Strictly isolated from domain logic to prevent circular import dependencies.
"""

import os
from datetime import datetime

# Base output directory definition
BASE_OUTPUT_DIR = "outputs"

# Dynamic run directory based on initialization timestamp
_timestamp = datetime.now().strftime("%y.%m.%d-%H.%M.%S")
RUN_DIR = os.path.join(BASE_OUTPUT_DIR, f"RUN {_timestamp}")

# Domain-specific subdirectories
LOGS_DIR = os.path.join(RUN_DIR, "logs")
GRAPHS_DIR = os.path.join(RUN_DIR, "graphs")
EMP_DIR = os.path.join(RUN_DIR, "EMP Files")
CSV_DIR = os.path.join(RUN_DIR, "csv results")