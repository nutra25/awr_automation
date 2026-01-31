import config
import logging
from enum import Enum

logger = logging.getLogger("awr_automation")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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
    global sp_mag, sp_ang, lp_mag, lp_ang
    sp_mag = ["0",]
    sp_ang = ["0",]
    lp_mag = ["0",]
    lp_ang = ["0",]

def iteration():
    class Type(Enum):
        LOADPULL = 0
        SOURCEPULL = 1

    def run_pull(pull_type: Type, iteration: int):
        logger.info(f"Iteration {i + 1} {pull_type.name} Radius: {config.radius_list[iteration]}")

    for i in range(config.iteration_count):
        #logger.info(f"Iteration {i+1}")
        run_pull(pull_type=Type.SOURCEPULL, iteration=i)
        run_pull(pull_type=Type.LOADPULL, iteration=i)

def set_state_variable(var_no: int, var_value: int):
    logger.info(f"State:{(var_no + 1) * (var_value + 1)} Set state var {config.state_var[var_no].name} as {config.state_var[var_no].value[var_value]}")  # add a set code
    pass

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