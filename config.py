"""
config.py
Defines the hierarchical configuration structure for the AWR Automation project.
Utilizes dataclasses to provide strictly typed and structured configuration nodes.
Fully integrated with domain-specific configuration objects.
"""
import os
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

import objects
from objects import generate_sweep_values

# Import domain-specific configuration nodes
from rfdesign.loadpull.iteration_point_selector import BroadbandOptimumSelector, PointSelectorConfig
from rfdesign.loadpull.state_result_selector import LastIterationStrategy, ResultSelectorConfig
from rfdesign.loadpull.tuner_utils import TunerConfig, TunerSideConfig
from paths import RUN_DIR, CSV_DIR, GRAPHS_DIR, EMP_DIR

# ---------------------------------------------------------
# Configuration Dataclasses (Tree Structure)
# ---------------------------------------------------------

@dataclass
class HandlersConfig:
    schematic_name: str

@dataclass
class SequenceConfig:
    schematic_name: str
    tuner_settings: TunerConfig  # Updated from Dict to TunerConfig
    measurement_config: List[Dict[str, Any]]
    graph_name_pattern: str
    point_selector: Any
    iteration_count: int
    radius_list: Tuple[str, ...]

@dataclass
class LoadPullConfig:
    handlers: HandlersConfig
    sequence: SequenceConfig

@dataclass
class RfDesignConfig:
    loadpull: LoadPullConfig

@dataclass
class EngineConfig:
    schematic_name: str
    state_cons: List[objects.State]
    state_var: List[objects.State]
    measurement_config: List[Dict[str, Any]]
    iteration_count: int
    run_dir: str
    graphs_dir: str
    emp_dir: str

@dataclass
class AppConfig:
    awr_path: str
    project_template_path: str
    engine: EngineConfig
    rf_design: RfDesignConfig

# ---------------------------------------------------------
# Configuration Instantiation
# ---------------------------------------------------------

_SCHEMATIC_NAME = "Load_Pull_Template"
_ITERATION_COUNT = 3
_RADIUS_LIST = ("0.99", "0.60", "0.30")
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
    engine=EngineConfig(
        schematic_name=_SCHEMATIC_NAME,
        state_cons=[
            objects.State(
                name="Frekans (GHz)",
                value=generate_sweep_values(12.7, 13.25, 0.05),
                type=objects.StateType.RF_FREQUENCY,
            ),
            objects.State(
                name="VDS",
                value="40",
                element=[objects.Element(name="DCVS.VDS", arg="V")]
            )
        ],
        state_var=[
            objects.State(
                name="P_in (dBm)",
                value="30",
                element=[objects.Element(name="PORT1.P1", arg="Pwr")]
            ),
            objects.State(
                name="VGS (V)",
                value="-2.9",
                element=[objects.Element(name="DCVS.VGS", arg="V")]
            )
        ],
        measurement_config=_MEASUREMENT_CONFIG,
        iteration_count=_ITERATION_COUNT,
        run_dir=RUN_DIR,
        graphs_dir=GRAPHS_DIR,
        emp_dir=EMP_DIR
    ),
    rf_design=RfDesignConfig(
        loadpull=LoadPullConfig(
            handlers=HandlersConfig(
                schematic_name=_SCHEMATIC_NAME
            ),
            sequence=SequenceConfig(
                schematic_name=_SCHEMATIC_NAME,
                tuner_settings=_TUNER_CONFIG,
                measurement_config=_MEASUREMENT_CONFIG,
                graph_name_pattern=_GRAPH_NAME_PATTERN,
                # Injecting the specific config node for the point selector
                point_selector=BroadbandOptimumSelector(config=PointSelectorConfig(show_plot=True)),
                iteration_count=_ITERATION_COUNT,
                radius_list=_RADIUS_LIST
            )
        )
    )
)

if __name__ == "__main__":
    import sys
    from logger.logger import LOGGER
    LOGGER.info("├── Testing final configuration tree integration...")
    try:
        LOGGER.info(f"│   ├── Tuner Source Name: {app_config.rf_design.loadpull.sequence.tuner_settings.source.name}")
        LOGGER.info(f"│   ├── Point Selector Plot Status: {app_config.rf_design.loadpull.sequence.point_selector.config.show_plot}")
        LOGGER.info("└── Configuration integration test completed successfully.")
    except Exception as e:
        LOGGER.critical(f"└── Configuration test failed: {e}")
        sys.exit(1)