import objects

##################################################
# SCRIPT SETTING !DONT_TOUCH!
host = "127.0.0.1"
port = 50505
udp_timeout_s = 100
down_blast = 60
##################################################

##################################################
# PROJECT SETTINGS
schematic_name = "VDS40_Load_Pull"
##################################################

##################################################
# STATE CONSTANTS
state_cons = [objects.State() for i in range(1)]

state_cons[0].name = "VDS"
state_cons[0].element = [objects.Element() for _ in range(1)]
state_cons[0].value = ("40",)
state_cons[0].element[0].name = "DCVS.VDS"
state_cons[0].element[0].arg = "V"
##################################################

##################################################
# STATE VARIABLES
state_var = [ objects.State() for _ in range(1) ]

state_var[0].name = "Frekans"
state_var[0].element = [objects.Element() for _ in range(2)]
state_var[0].value = ("13", "13.5", "14")
state_var[0].element[0].name = "HBTUNER3.SourcePull"
state_var[0].element[0].arg = "Fo"
state_var[0].element[1].name = "HBTUNER3.LoadPull"
state_var[0].element[1].arg = "Fo"
##################################################

##################################################
# ITERATION SETTINGS
iteration_count = 3
radius_list = ("0.99", "0.40", "0.30")
##################################################
