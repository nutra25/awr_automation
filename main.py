import config
import logging
from enum import Enum
import random

logger = logging.getLogger("awr_automation")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class Type(Enum):
    LOADPULL = 0
    SOURCEPULL = 1

def state_count_calculator():
    out = 1
    for i in range(len(config.state_var)):
        out = out * len(config.state_var[i].value)
    return out

def initial():
    pass

def set_state_constant():
    for i in range(len(config.state_cons)):
        logger.info(f"Set state constant {config.state_cons[i].name}")  # SET kodu ekle

def initial_iteration():
    global sp_point, sp_mag, sp_ang, lp_point, lp_mag, lp_ang
    sp_point = []
    sp_mag = ["0",]
    sp_ang = ["0",]
    lp_point = []
    lp_mag = ["0",]
    lp_ang = ["0",]

def get_graph_data(iteration: int, pull_type: Type, marker: str):
    logger.info(f"GET| GRAPH: it{iteration}_{"load_pull" if Type.LOADPULL == pull_type else "source_pull"} MARKER:{marker}")
    point = f"{random.randint(0, 100)}"  #Bu bilgiler awr_marker_readerdan gelecek!!
    mag = f"{round(random.uniform(0, 1), 3)}"    #Bu bilgiler awr_marker_readerdan gelecek!!
    ang = f"{random.randint(-180, 180)}"    #Bu bilgiler awr_marker_readerdan gelecek!!
    return point, mag, ang  #Bu bilgiler awr_marker_readerdan gelecek!!



def iteration():
    global sp_point, sp_mag, sp_ang, lp_point, lp_mag, lp_ang
    def run_pull(pull_type: Type, iteration: int):
        logger.info(f"Iteration {i + 1} {pull_type.name} Radius: {config.radius_list[iteration]}")

    for i in range(config.iteration_count):
        #logger.info(f"Iteration {i+1}")
        run_pull(pull_type=Type.SOURCEPULL, iteration=i)
        sp_point, sp_mag, sp_ang = get_graph_data(pull_type=Type.SOURCEPULL, iteration=i, marker="m1")
        logger.info(f"Point:{sp_point}, Mag:{sp_mag}, Ang:{sp_ang}")
        run_pull(pull_type=Type.LOADPULL, iteration=i)
        lp_point, lp_mag, lp_ang =get_graph_data(pull_type=Type.LOADPULL, iteration=i, marker="m1")
        logger.info(f"Point:{lp_point}, Mag:{lp_mag}, Ang:{lp_ang}")

def set_state_variable(var_no: int, var_value: int):
    logger.info(f"State:{(var_no + 1) * (var_value + 1)} Set state var {config.state_var[var_no].name} as {config.state_var[var_no].value[var_value]}")  # add a set code

def update_element(name: str, arg: str, value: str,):
    logger.info(f"UPDATE| ELEMENT:{name} {arg}={value}")


def main():
    initial() # For future usage
    set_state_constant()

    for i in range(len(config.state_var)):
        for j in range(len(config.state_var[i].value)):
            set_state_variable(i, j)
            initial_iteration() # For future usage
            iteration()

    logger.info("DONE")


if __name__ == "__main__":
    main()