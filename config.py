"""
config.py
Defines the hierarchical configuration structure for the AWR Automation project.
Utilizes dataclasses to provide strictly typed and structured configuration nodes.
Fully integrated with domain-specific configuration objects imported directly from their modules.
"""
from dataclasses import dataclass
from typing import List, Dict, Any

from engine.models import State, StateType, Element
from engine.utils import generate_sweep_values
from paths import RUN_DIR, CSV_DIR, GRAPHS_DIR, EMP_DIR

# Import encapsulated domain-specific configuration nodes
from rfdesign.loadpull.iteration_point_selector import BroadbandOptimumSelector, PointSelectorConfig
from rfdesign.loadpull.state_result_selector import LastIterationStrategy, ResultSelectorConfig
from rfdesign.loadpull.tuner_utils import TunerConfig, TunerSideConfig

from rfdesign.loadpull.handlers import HandlersConfig
from rfdesign.loadpull.sequence import SequenceConfig, WizardSettingsConfig
from rfdesign.loadpull.manager import LoadPullConfig
from rfdesign.loadpull.create_new_loadpull_project import CreateProjectConfig

# ---------------------------------------------------------
# Global Configuration Dataclasses (Upper Tree Structure)
# ---------------------------------------------------------

@dataclass
class RfDesignConfig:
    """Configuration node managing all RF design strategies and macros."""
    loadpull: LoadPullConfig
    project_generation: CreateProjectConfig

@dataclass
class EngineConfig:
    """Configuration node for the global simulation engine."""
    schematic_name: str
    state_cons: List[State]
    state_var: List[State]
    measurement_config: List[Dict[str, Any]]
    iteration_count: int
    run_dir: str
    graphs_dir: str
    emp_dir: str

@dataclass
class AppConfig:
    """Root configuration node for the entire application."""
    awr_path: str
    project_template_path: str
    engine: EngineConfig
    rf_design: RfDesignConfig

# ---------------------------------------------------------
# Configuration Instantiation (Dependency Injection Root)
# ---------------------------------------------------------

_SCHEMATIC_NAME = "Load_Pull_Template"
_ITERATION_COUNT = 3
_RADIUS_LIST = (0.99, 0.60, 0.30)
_GRAPH_NAME_PATTERN = "it{iter}_{type}_pull"

# Instantiating strictly-typed Tuner Configuration
_TUNER_CONFIG = TunerConfig(
    source=TunerSideConfig(name="HBTUNER3.SourceTuner", prefix_mag="Mag", prefix_ang="Ang", harmonics_to_track=[1]),
    load=TunerSideConfig(name="HBTUNER3.LoadTuner", prefix_mag="Mag", prefix_ang="Ang", harmonics_to_track=[1])
)

_MEASUREMENT_CONFIG = [
    {"header": "PLoad [dBm]", "graph": "Results", "marker": "MinPwr", "index": 1},
    {"header": "PAE [%]", "graph": "Results", "marker": "MinPAE", "index": 1}
]

app_config = AppConfig(
    awr_path=r"C:\Program Files (x86)\AWR\AWRDE\19\MWOffice.exe",
    project_template_path=r"C:\Users\aliutkay\OneDrive\Masaüstü\test\loadpull.emp",

    # Engine Settings
    engine=EngineConfig(
        schematic_name=_SCHEMATIC_NAME,
        state_cons=[
            State(
                name="Frekans (GHz)",
                value=generate_sweep_values(12.7, 13.25, 0.05),
                type=StateType.RF_FREQUENCY,
            ),
            State(
                name="VDS",
                value="40",
                element=[Element(name="DCVS.VDS", arg="V")]
            )
        ],
        state_var=[
            State(
                name="P_in (dBm)",
                value="30",
                element=[Element(name="PORT1.P1", arg="Pwr")]
            ),
            State(
                name="VGS (V)",
                value="-2.9",
                element=[Element(name="DCVS.VGS", arg="V")]
            )
        ],
        measurement_config=_MEASUREMENT_CONFIG,
        iteration_count=_ITERATION_COUNT,
        run_dir=RUN_DIR,
        graphs_dir=GRAPHS_DIR,
        emp_dir=EMP_DIR
    ),

    # Domain Specific Strategies (RF Design)
    rf_design=RfDesignConfig(
        loadpull=LoadPullConfig(
            handlers=HandlersConfig(
                schematic_name=_SCHEMATIC_NAME
            ),
            sequence=SequenceConfig(
                schematic_name=_SCHEMATIC_NAME,
                tuner_settings=_TUNER_CONFIG,
                wizard_settings=WizardSettingsConfig(
                    max_harmonic=1,
                    overwrite_data_file=True,
                    data_file_pattern="{side}_pull_data_{iter}",
                    density="Extra fine"
                ),
                measurement_config=_MEASUREMENT_CONFIG,
                graph_name_pattern=_GRAPH_NAME_PATTERN,
                point_selector=BroadbandOptimumSelector(config=PointSelectorConfig(show_plot=True)),
                iteration_count=_ITERATION_COUNT,
                radius_list=_RADIUS_LIST
            )
        ),
        project_generation=CreateProjectConfig(
            library_path="MA_RFP",
            schematic_name=_SCHEMATIC_NAME,
            target_element="CURTICE3.CFH1",
            element_library="BP:\\Circuit Elements\\Libraries\\*MA_RFP -- v0.0.2.5\\GaN Product\\CGHV1F006S",
            node_mapping={1: 1, 2: [2], 3: [3, 4, 5, 6, 7]},
            input_port_target="PORT_PS1.P1",
            input_port_replacement="PORT1",
            iterations=_ITERATION_COUNT,
            save_path=r"C:\Users\aliutkay\OneDrive\Masaüstü\test\loadpull.emp"
        )
    )
)

if __name__ == "__main__":
    import sys
    from logger.logger import LOGGER
    LOGGER.info("├── Testing final configuration tree integration...")
    try:
        LOGGER.info(f"│   ├── App Executable Path: {app_config.awr_path}")
        LOGGER.info(f"│   ├── Tuner Source Name: {app_config.rf_design.loadpull.sequence.tuner_settings.source.name}")
        LOGGER.info(f"│   ├── Point Selector Plot Status: {app_config.rf_design.loadpull.sequence.point_selector.config.show_plot}")
        LOGGER.info(f"│   ├── Project Generation Library: {app_config.rf_design.project_generation.library_path}")
        LOGGER.info("└── Configuration integration test completed successfully.")
    except Exception as e:
        LOGGER.critical(f"└── Configuration test failed: {e}")
        sys.exit(1)