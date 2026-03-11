from awr import Awr
from awr.graph import GraphType

awr = Awr(r"C:\Program Files (x86)\AWR\AWRDE\19\MWOffice.exe")
#awr.project.new_project_with_library(library_name="MA_RFP")
awr.wizard.create_load_pull_template()
awr.schematic.element.replace_element("Load_Pull_Template","CURTICE3.CFH1",{1: 1, 2: [2], 3: [3, 4, 5, 6, 7]},"BP:\\Circuit Elements\\Libraries\\*MA_RFP -- v0.0.2.5\\GaN Product\\CGHV1F006S")

