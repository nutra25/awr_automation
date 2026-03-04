"""
config.py
Defines the hierarchical configuration structure for the AWR Automation project.
Utilizes Pydantic to provide strictly typed, validated, and structured configuration nodes.
Fully integrated with domain-specific configuration objects imported directly from their modules.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any

from engine.models import State, StateType, Element
from engine.utils import generate_sweep_values
from core.paths import RUN_DIR, GRAPHS_DIR, EMP_DIR

from rfdesign.loadpull.iteration_point_selector import BroadbandOptimumSelector, PointSelectorConfig, MaxMeasurementSelector
from rfdesign.loadpull.tuner_utils import TunerConfig, TunerSideConfig
from rfdesign.loadpull.handlers import HandlersConfig
from rfdesign.loadpull.sequence import SequenceConfig, WizardSettingsConfig
from rfdesign.loadpull.manager import LoadPullConfig
from rfdesign.loadpull.create_new_loadpull_project import CreateProjectConfig

class RfDesignConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    loadpull: LoadPullConfig
    project_generation: Any

class EngineConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    schematic_name: str
    state_cons: List[State]
    state_var: List[State]
    measurement_config: List[Dict[str, Any]]
    iteration_count: int = Field(..., gt=0)
    run_dir: str
    graphs_dir: str
    emp_dir: str

class AppConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    awr_path: str = Field(..., description="Absolute path to the AWR executable")
    project_template_path: str = Field(..., description="Absolute path to the starting .emp template")
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
    {"header": "PLoad [dBm] (min)", "graph": "Results", "marker": "MinPwr", "update-type":"MIN", "index": 1},
    {"header": "PAE [%] (min)", "graph": "Results", "marker": "MinPAE", "update-type":"MIN", "index": 1},
    {"header": "PLoad [dBm] (max)", "graph": "Results", "marker": "MaxPwr", "update-type": "MAX", "index": 1},
    {"header": "PAE [%] (max)", "graph": "Results", "marker": "MaxPAE", "update-type": "MAX", "index": 1}
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
                value=generate_sweep_values(13.1, 13.1, 0.05),
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
                value="31",
                element=[Element(name="PORT1.P1", arg="Pwr")]
            ),
            State(
                name="VGS (V)",
                value="-2.85",
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
                point_selector=MaxMeasurementSelector(
                    config=PointSelectorConfig(
                        measurement_name="G_LPCMMAX(PAE" # Başka bir ölçüm isterseniz burayı değiştirebilirsiniz
                    )
                ),
                #BroadbandOptimumSelector(config=PointSelectorConfig(show_plot=True)),
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
    from core.logger import logger
    logger.info("├── Testing final configuration tree integration...")
    try:
        logger.info(f"│   ├── App Executable Path: {app_config.awr_path}")
        logger.info(f"│   ├── Tuner Source Name: {app_config.rf_design.loadpull.sequence.tuner_settings.source.name}")
        logger.info(f"│   ├── Point Selector Plot Status: {app_config.rf_design.loadpull.sequence.point_selector.config.show_plot}")
        logger.info(f"│   ├── Project Generation Library: {app_config.rf_design.project_generation.library_path}")
        logger.info("└── Configuration integration test completed successfully.")
    except Exception as e:
        logger.critical(f"└── Configuration test failed: {e}")
        sys.exit(1)