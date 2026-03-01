"""
create_new_loadpull_project.py
Macro-orchestrator for generating a complete Load-Pull project environment from scratch.
Automates project initialization, schematic template generation, device replacement,
and the bulk creation of required graphs, data files, and measurements.
Strictly adheres to the tree-branch logging hierarchy.
"""

import sys
from typing import Dict, Any

from logger.logger import LOGGER
from awr.awr_driver import AWRDriver
from awr.graph.new_graph import GraphType
from awr.data_file.new_data_file import DataFileType

def create_loadpull_project(driver: AWRDriver, config: Dict[str, Any]) -> bool:
    """
    Executes the comprehensive sequence to build a Load-Pull project environment.

    Args:
        driver (AWRDriver): The central initialized AWR API driver.
        config (Dict[str, Any]): A dictionary containing parameters for the setup.
            Required keys: library_path, schematic_name, target_element,
                           element_library, node_mapping, iterations.

    Returns:
        bool: True if the entire project generation sequence succeeds, False otherwise.
    """
    LOGGER.info("├── Initiating Load-Pull Project Creation Sequence...")

    # Extract configuration parameters safely
    library_path = config.get("library_path", "")
    schematic_name = config.get("schematic_name", "Load_Pull_Template")
    target_element = config.get("target_element", "CFH1")
    element_library = config.get("element_library", "")
    node_mapping = config.get("node_mapping", {1: 1, 2: 2, 7: 1})
    iterations = config.get("iterations", 3)

    try:
        # 1. Initialize New Project with specific library
        LOGGER.info("│   ├── Step 1: Initializing new project environment...")
        if hasattr(driver.project, 'new_project_with_library'):
            driver.project.new_project_with_library(library_path)
        else:
            LOGGER.warning("│   │   ├── Method 'new_project_with_library' not explicitly found. Ensure it is integrated into ProjectManager.")

        # 2. Create Load Pull Template via Wizard
        LOGGER.info("│   ├── Step 2: Generating Load-Pull schematic template...")
        if hasattr(driver.wizard, 'create_load_pull_template'):
            template_success = driver.wizard.create_load_pull_template()
            if not template_success:
                LOGGER.error("│   └── Sequence aborted: Failed to generate schematic template.")
                return False
        else:
            LOGGER.warning(
                "│   │   ├── Method 'create_load_pull_template' not explicitly found. Ensure it is integrated into WizardManager.")

        # 3. Replace the default transistor/element with the target library component
        LOGGER.info(f"│   ├── Step 3: Replacing element '{target_element}' and applying routing matrix...")
        replacement_success = driver.circuit.replace_element(
            schematic_name=schematic_name,
            target=target_element,
            library_path=element_library,
            mapping=node_mapping
        )

        if not replacement_success:
            LOGGER.error("│   └── Sequence aborted: Element replacement failed.")
            return False

        # Replace the input port element
        LOGGER.info(f"│   ├── Step 3: Replacing element PORT_PS1.1 and applying routing matrix...")
        replacement_success = driver.circuit.replace_element(
            schematic_name=schematic_name,
            target="PORT_PS1.P1",
            element_name="PORT1",
            mapping=node_mapping
        )

        if not replacement_success:
            LOGGER.error("│   └── Sequence aborted: Element replacement failed.")
            return False

        # 4. Generate the required Data Files, Graphs, and Measurements (Iteration * 2)
        LOGGER.info(f"│   ├── Step 4: Generating operational infrastructure for {iterations} iterations...")

        for i in range(1, iterations + 1):
            # Iterate twice per iteration number (Once for Source Pull, Once for Load Pull)
            for pull_mode in ["source", "load"]:
                prefix = pull_mode

                # Dynamic Naming Convention
                df_name = f"{pull_mode}_pull_data_{i}"
                graph_name = f"it{i}_{prefix}_pull"
                source_doc = df_name  # The data file acts as the source document for the measurement
                meas_expr = "G_LPCM(PAE,0.5,12,50,0)[1,*]"  # Placeholder for the actual AWR measurement expression

                LOGGER.debug(f"│   │   ├── Setting up infrastructure for Iteration {i} ({prefix.capitalize()} Pull)")

                # 4.1. Add New Data File
                driver.data_file.add_new(file_name=df_name, file_type=DataFileType.GMDIFD)

                # 4.2. Add New Graph
                driver.graph.add_new_graph(graph_name=graph_name, graph_type=GraphType.SMITH_CHART)

                # 4.3. Add Measurement to the Graph
                driver.graph.add_measurement(graph_name=graph_name, source_name=source_doc, measurement_expression=meas_expr)

        driver.graph.add_new_graph(graph_name="Results", graph_type=GraphType.RECTANGULAR)

        driver.graph.add_measurement(graph_name="Results", source_name=f"{schematic_name}.AP_HB", measurement_expression="PAE(PORT_1,PORT_2)")
        driver.graph.add_measurement(graph_name="Results", source_name=f"{schematic_name}.AP_HB", measurement_expression="DB(PT(PORT_2))")

        driver.graph.add_and_move_marker(graph_name="Results", measurement_name="PAE(PORT_1,PORT_2)",marker_name="MinPAE",action="MIN")
        driver.graph.add_and_move_marker(graph_name="Results", measurement_name="PAE(PORT_1,PORT_2)",marker_name="MaxPAE",action="MAX")
        driver.graph.add_and_move_marker(graph_name="Results", measurement_name="DB(PT(PORT_2))",marker_name="MinPwr",action="MIN")
        driver.graph.add_and_move_marker(graph_name="Results", measurement_name="DB(PT(PORT_2))",marker_name="MaxPwr",action="MAX")


        LOGGER.info("└── Load-Pull Project Creation Sequence Finalized Successfully.")
        driver.project.save_current_project_as(save_path= r"C:\Users\aliutkay\OneDrive\Masaüstü\test\loadpull.emp")
        return True

    except Exception as e:
        LOGGER.error(f"└── Unhandled exception during project creation sequence: {e}")
        return False


# Standalone Test Execution Block
if __name__ == "__main__":
    import pyawr.mwoffice as mwoffice

    LOGGER.info("Starting standalone test sequence for create_new_loadpull_project.py module.")

    try:
        # Initialize the AWR Driver (Assumes an active MWOffice session exists)
        test_driver = AWRDriver()

        # Define the centralized configuration dictionary
        test_config = {
            "library_path": "MA_RFP",
            "schematic_name": "Load_Pull_Template",
            "target_element": "CURTICE3.CFH1",
            "element_library": "BP:\\Circuit Elements\\Libraries\\*MA_RFP -- v0.0.2.5\\GaN Product\\CGHV1F006S",
            "node_mapping": {1: 1, 2: [2], 3: [3, 4, 5, 6, 7]},
            "iterations": 3
        }

        # Execute the macro orchestrator
        result = create_loadpull_project(test_driver, test_config)

        if result:
            LOGGER.info("└── Test execution sequence completed successfully.")
        else:
            LOGGER.warning("└── Test execution completed, but sequence returned False.")

    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed: {ex}")
        sys.exit(1)