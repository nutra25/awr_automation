import os
from datetime import datetime
from paths import *

import objects
from objects import generate_sweep_values
from rfdesign.loadpull.iteration_point_selector import BroadbandOptimumSelector
from rfdesign.loadpull.state_result_selector import LastIterationStrategy

##################################################
# PROJECT SETTINGS
SCHEMATIC_NAME: str = "VDS40_Load_Pull"
##################################################

##################################################
# STATE CONSTANTS
STATE_CONS = [
    objects.State(
        name="Frekans (GHz)",
        value=generate_sweep_values(12.7,13.25,0.05),
        type=objects.StateType.RF_FREQUENCY,
    ),
    objects.State(
        name="VDS",
        value="40",
        element=[
            objects.Element(name="DCVS.VDS", arg="V")
        ]
    )
]
##################################################

##################################################
# STATE VARIABLES
STATE_VAR = [
    objects.State(
        name="P_in (dBm)",
        value="30",
        element=[
            objects.Element(name="PORT1.P1", arg="Pwr")
        ]
    ),
    objects.State(
        name="VGS (V)",
        value="-2.9",
        element=[
            objects.Element(name="DCVS.VGS", arg="V"),
        ]
    )
]
##################################################

##################################################
# ITERATION SETTINGS
POINT_SELECTOR = BroadbandOptimumSelector()
FINAL_STRATEGY = LastIterationStrategy()
ITERATION_COUNT: int = 2
RADIUS_LIST: tuple = ("0.99", "0.60", "0.30")
GRAPH_NAME_PATTERN = "it{iter}_{type}_pull"

WIZARD_DEFAULTS = {
    "LP_MaxHarmonic": 1,
    "LP_Density": "Extra fine",
    "LP_OverwriteDataFile": True,
}

TUNER_SETTINGS = {
    "SOURCE": {
        "name": "HBTUNER3.SourceTuner",
        "prefix_mag": "Mag",
        "prefix_ang": "Ang",
        "harmonics_to_track": [1]
    },
    "LOAD": {
        "name": "HBTUNER3.LoadTuner",
        "prefix_mag": "Mag",
        "prefix_ang": "Ang",
        "harmonics_to_track": [1]
    }
}
##################################################

##################################################
# MEASUREMENT_CONFIG
MEASUREMENT_CONFIG = [
    {
        "header": "PLoad [dBm]",
        "graph": "Results",
        "marker": "m1",
        "index": 1
    },
    {
        "header": "PAE [%]",
        "graph": "Results",
        "marker": "m2",
        "index": 1
    }
]
##################################################

##################################################
# RESULT DATA SAVING SETTINGS
FILENAME: str = os.path.join(CSV_DIR, "simulation_results.csv")
##################################################