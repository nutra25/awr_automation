import objects
from objects import generate_sweep_values

##################################################
# SCRIPT SETTING !DONT_TOUCH!
HOST: str = "127.0.0.1"
PORT: int = 50505
UDP_TIMEOUT: int = 100
DOWN_BLAST: int = 60
##################################################

##################################################
# PROJECT SETTINGS
SCHEMATIC_NAME: str = "VDS40_Load_Pull"
##################################################

##################################################
# STATE CONSTANTS
STATE_CONS = [
    objects.State(
        name="VDS",
        value="50",
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
        name="Frekans (GHz)",
        value=generate_sweep_values(start=12.8, stop=12.8, step=0.25),
        element=[
            objects.Element(name="HBTUNER3.SourceTuner", arg="Fo"),
            objects.Element(name="HBTUNER3.LoadTuner", arg="Fo")
        ]
    ),
    objects.State(
        name="P_in (dBm)",
        value=generate_sweep_values(start=30, stop=30, step=1),
        element=[
            objects.Element(name="PORT1.P1", arg="Pwr")
        ]
    ),
    objects.State(
        name="VGS (V)",
        value=generate_sweep_values(start=-2.71, stop=-2.71, step=-0.25),
        element=[
            objects.Element(name="DCVS.VGS", arg="V"),
        ]
    )
]
##################################################

##################################################
# ITERATION SETTINGS
ITERATION_COUNT: int = 3
RADIUS_LIST: tuple = ("0.99", "0.40", "0.30")
MARKER: str = "m1"
##################################################
