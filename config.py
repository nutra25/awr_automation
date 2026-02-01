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
        name="Frekans (GHz)",
        value=generate_sweep_values(start=13, stop=13.25, step=0.25),
        element=[
            objects.Element(name="HBTUNER3.SourcePull", arg="Fo"),
            objects.Element(name="HBTUNER3.LoadPull", arg="Fo")
        ]
    ),
    objects.State(
        name="P_in (dBm)",
        value=generate_sweep_values(start=27, stop=29, step=1),
        element=[
            objects.Element(name="PORT1.P1", arg="Pwr")
        ]
    ),
    objects.State(
        name="VGS (V)",
        value=generate_sweep_values(start=-2, stop=-2.25, step=-0.25),
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
