"""
create_new_loadpull_project.py
Macro-orchestrator for generating a complete Load-Pull project environment from scratch.
Automates project initialization, schematic template generation, device replacement,
and the bulk creation of required graphs, data files, and measurements.
Strictly adheres to the tree-branch logging hierarchy and Context architecture.
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field
from core.logger import logger
from awr.graph.manager import GraphType
from awr.data_file.new_data_file import DataFileType


@dataclass
class CreateProjectConfig:
    """Configuration node for generating a new Load-Pull project."""
    library_path: str = "MA_RFP"
    schematic_name: str = "Load_Pull_Template"
    target_element: str = "CFH1"
    element_library: str = ""
    node_mapping: Dict[int, Any] = field(default_factory=lambda: {1: 1, 2: 2, 7: 1})
    input_port_target: str = "PORT_PS1.P1"
    input_port_replacement: str = "PORT1"
    iterations: int = 3

    # Graph & Measurement settings
    meas_expr_pae_contour: str = "G_LPCM(PAE,0.5,12,50,0)[1,*]"
    results_graph_name: str = "Results"
    results_pae_meas: str = "PAE(PORT_1,PORT_2)"
    results_pwr_meas: str = "DB(PT(PORT_2))"
    pull_modes: List[str] = field(default_factory=lambda: ["source", "load"])

    # Final output settings
    save_path: str = r"C:\Users\aliutkay\OneDrive\Masaüstü\test\loadpull.emp"


def create_loadpull_project(context: Any) -> bool:
    """
    Executes the comprehensive sequence to build a Load-Pull project environment.
    Utilizes the global AutomationContext for dependencies and configuration.
    """
    logger.info("├── Initiating Load-Pull Project Creation Sequence...")

    try:
        driver = context.driver
        config = context.config.rf_design.project_generation

        # Initialize New Project with specific library
        logger.info("│   ├── Step 1: Initializing new project environment...")
        if hasattr(driver.project, 'new_project_with_library'):
            driver.project.new_project_with_library(config.library_path)
        else:
            logger.warning("│   │   ├── Method 'new_project_with_library' not explicitly found in Manager.")

        # Create Load Pull Template via Wizard
        logger.info("│   ├── Step 2: Generating Load-Pull schematic template...")
        if hasattr(driver.wizard, 'create_load_pull_template'):
            template_success = driver.wizard.create_load_pull_template()
            if not template_success:
                logger.error("│   └── Sequence aborted: Failed to generate schematic template.")
                return False
        else:
            logger.warning("│   │   ├── Method 'create_load_pull_template' not explicitly found in Manager.")

        # Replace the default transistor/element with the target library component
        logger.info(f"│   ├── Step 3: Replacing element '{config.target_element}' and applying routing matrix...")
        replacement_success = driver.circuit.replace_element(
            schematic_name=config.schematic_name,
            target=config.target_element,
            library_path=config.element_library,
            mapping=config.node_mapping
        )

        if not replacement_success:
            logger.error("│   └── Sequence aborted: Element replacement failed.")
            return False

        # Replace the input port element
        logger.info(f"│   ├── Step 3: Replacing element {config.input_port_target} and applying routing matrix...")
        replacement_success = driver.circuit.replace_element(
            schematic_name=config.schematic_name,
            target=config.input_port_target,
            element_name=config.input_port_replacement,
            mapping=config.node_mapping
        )

        if not replacement_success:
            logger.error("│   └── Sequence aborted: Input port replacement failed.")
            return False

        # Generate the required Data Files, Graphs, and Measurements
        logger.info(f"│   ├── Step 4: Generating operational infrastructure for {config.iterations} iterations...")

        for i in range(1, config.iterations + 1):
            for pull_mode in config.pull_modes:
                df_name = f"{pull_mode}_pull_data_{i}"
                graph_name = f"it{i}_{pull_mode}_pull"
                source_doc = df_name

                logger.debug(f"│   │   ├── Setting up infrastructure for Iteration {i} ({pull_mode.capitalize()} Pull)")

                driver.data_file.add_new(file_name=df_name, file_type=DataFileType.GMDIFD)
                driver.graph.add_new_graph(graph_name=graph_name, graph_type=GraphType.SMITH_CHART)
                driver.graph.add_measurement(graph_name=graph_name, source_name=source_doc, measurement_expression=config.meas_expr_pae_contour)

        # Set up final results graph
        driver.graph.add_new_graph(graph_name=config.results_graph_name, graph_type=GraphType.RECTANGULAR)
        source_hb = f"{config.schematic_name}.AP_HB"

        driver.graph.add_measurement(graph_name=config.results_graph_name, source_name=source_hb, measurement_expression=config.results_pae_meas)
        driver.graph.add_measurement(graph_name=config.results_graph_name, source_name=source_hb, measurement_expression=config.results_pwr_meas)

        # Add and move markers dynamically based on the configured names
        driver.graph.add_and_move_marker(graph_name=config.results_graph_name, measurement_name=config.results_pae_meas, marker_name="MinPAE", action="MIN")
        driver.graph.add_and_move_marker(graph_name=config.results_graph_name, measurement_name=config.results_pae_meas, marker_name="MaxPAE", action="MAX")
        driver.graph.add_and_move_marker(graph_name=config.results_graph_name, measurement_name=config.results_pwr_meas, marker_name="MinPwr", action="MIN")
        driver.graph.add_and_move_marker(graph_name=config.results_graph_name, measurement_name=config.results_pwr_meas, marker_name="MaxPwr", action="MAX")

        logger.info("└── Load-Pull Project Creation Sequence Finalized Successfully.")
        driver.project.save_current_project_as(save_path=config.save_path)
        return True

    except Exception as e:
        logger.error(f"└── Unhandled exception during project creation sequence: {e}")
        return False