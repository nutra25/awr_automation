import objects
from objects import generate_sweep_values
import logging

##################################################
# SCRIPT SETTING !DONT_TOUCH!

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
        value="13.1",
        type=objects.StateType.RF_FREQUENCY,
    ),
    objects.State(
        name="P_in (dBm)",
        value="30",
        element=[
            objects.Element(name="PORT1.P1", arg="Pwr")
        ]
    ),
    objects.State(
        name="VGS (V)",
        value="-2.745",
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
MARKER: str = "m2"
##################################################

##################################################
#LOGGER STYLES AND COLORS
# STYLE AND RESET
RESET = "\033[0m"
BOLD  = "\033[1m"
UNDERLINE = "\033[4m"
# STANDART COLORS
RED    = "\033[31m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
BLUE   = "\033[34m"
MAGENTA = "\033[35m"
CYAN   = "\033[36m"
# BRIGHT COLORS
B_RED    = "\033[91m"
B_GREEN  = "\033[92m"
B_YELLOW = "\033[93m"
B_BLUE   = "\033[94m"
B_MAGENTA = "\033[95m"
B_CYAN   = "\033[96m"
GRAY     = "\033[90m"
# BACKGROUND COLORS
BG_RED    = "\033[41m"
BG_GREEN  = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE   = "\033[44m"
##################################################

##################################################
# LOGGING CONFIGURATION
# Configures output to both console and a persistent log file.
# Format: Date Time | Log Level | Message

logging.basicConfig(
    level=logging.INFO,
    format=f'{BOLD}{GRAY}[31;20m%(asctime)s | %(levelname)-1s |{RESET} %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        # File Handler: Overwrites the log file on each new run (mode='w').
        logging.FileHandler("simulation.log", mode='w', encoding='utf-8'),

        # Stream Handler: Outputs logs to the console standard output.
        logging.StreamHandler()
    ]
)
LOGGER = logging.getLogger("awr_automation")
##################################################