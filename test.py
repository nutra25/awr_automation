from awr import Awr
from awr.graph import GraphType

awr = Awr(r"C:\Program Files (x86)\AWR\AWRDE\19\MWOffice.exe")

awr.project.new_project_with_library(library_name="MA_RFP")
awr.wizard.create_load_pull_template()