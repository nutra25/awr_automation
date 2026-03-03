"""
paths.py
Defines fundamental directory structures and dynamic paths for the project.
Utilizes a structured configuration node to manage output directories,
preventing global state pollution and supporting dependency injection.
"""

import os
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class PathsConfig:
    """
    Configuration node for project path management.
    Calculates dynamic run directories upon instantiation.
    """
    base_output_dir: str = "../outputs"
    run_dir: str = field(init=False)
    logs_dir: str = field(init=False)
    graphs_dir: str = field(init=False)
    emp_dir: str = field(init=False)
    csv_dir: str = field(init=False)

    def __post_init__(self) -> None:
        """
        Constructs the internal directory hierarchy based on the initialization timestamp.
        """
        timestamp = datetime.now().strftime("%y.%m.%d-%H.%M.%S")
        self.run_dir = os.path.join(self.base_output_dir, f"RUN {timestamp}")

        # Domain-specific subdirectories
        self.logs_dir = os.path.join(self.run_dir, "logs")
        self.graphs_dir = os.path.join(self.run_dir, "graphs")
        self.emp_dir = os.path.join(self.run_dir, "EMP Files")
        self.csv_dir = os.path.join(self.run_dir, "csv results")


# Default global instance to ensure backward compatibility for modules
# that import these variables directly rather than using dependency injection.
default_paths = PathsConfig()

BASE_OUTPUT_DIR = default_paths.base_output_dir
RUN_DIR = default_paths.run_dir
LOGS_DIR = default_paths.logs_dir
GRAPHS_DIR = default_paths.graphs_dir
EMP_DIR = default_paths.emp_dir
CSV_DIR = default_paths.csv_dir


if __name__ == "__main__":
    import sys
    print("├── Starting standalone test sequence for paths.py")
    try:
        test_config = PathsConfig(base_output_dir="test_outputs")
        print(f"│   ├── Generated Run Directory: {test_config.run_dir}")
        print(f"│   ├── Generated Logs Directory: {test_config.logs_dir}")
        print("└── Test execution sequence completed successfully")
    except Exception as ex:
        print(f"└── Test execution failed: {ex}")
        sys.exit(1)