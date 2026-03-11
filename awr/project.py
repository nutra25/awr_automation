import os
from typing import Optional
from .awr_component import AWRComponent


class Project(AWRComponent):

    def new_project_with_library(self, library_name: str, library_version: Optional[str] = None) -> bool:
        try:
            if library_version:
                self.logger.debug(f"│   ├── Target version specified: {library_version}")
                self.app.NewWithProcessLibraryEx(library_name, library_version)
            else:
                self.logger.debug("│   ├── No specific version provided. Using default library loader.")
                self.app.NewWithProcessLibrary(library_name)

            self.logger.info("└── Successfully generated new project with the specified process library.")
            return True

        except Exception as e:
            self.logger.error(f"└── Failed to create new project with library '{library_name}'. Details: {e}")
            return False

    def open_project(self, project_path: str) -> bool:

        self.logger.info(f"├── Initiating project load operation from path: {project_path}")

        if not os.path.exists(project_path):
            self.logger.error(f"└── Aborting load operation. Specified project file does not exist: {project_path}")
            return False

        try:
            success = self.app.Open(project_path)

            if success:
                active_project_name = self.app.Project.Name
                self.logger.info(f"└── Successfully loaded the specified project file: {active_project_name}")
                return True
            else:
                self.logger.error("└── Project open operation returned a failure status (False).")
                return False

        except Exception as e:
            self.logger.error(f"└── Encountered a critical error during the project open operation: {e}")
            return False

    def save_project_as(self, save_path: str) -> None:
        absolute_save_path = os.path.abspath(save_path)

        self.logger.info(f"├── Initiating project save operation to target path: {absolute_save_path}")

        try:
            project = self.app.Project

            project.SaveAs(absolute_save_path)

            active_project_name = project.Name
            self.logger.info(f"└── Successfully saved active project as: {active_project_name}")

        except Exception as e:
            self.logger.error(f"└── Failed to execute project save operation. Error details: {e}")

    def perform_simulation(self) -> bool:

        try:
            project = self.app.Project
            self.logger.debug("│   ├── Starting Simulation (Analyze)...")
            simulator = project.Simulator
            simulator.Analyze()
            self.logger.debug("│   ├── Simulation Completed.")
            return True
        except Exception as sim_error:
            self.logger.critical(f"│   └── Simulation FAILED: {sim_error}")
            raise RuntimeError(f"Simulation execution failed: {sim_error}")