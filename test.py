from awr import Awr
from awr.graph import GraphType

awr = Awr(r"C:\Program Files (x86)\AWR\AWRDE\19\MWOffice.exe")
#awr.project.new_project_with_library(library_name="MA_RFP")
#awr.wizard.create_load_pull_template()
#awr.schematic.element.replace_element("Load_Pull_Template","CURTICE3.CFH1",{1: 1, 2: [2], 3: [3, 4, 5, 6, 7]},"BP:\\Circuit Elements\\Libraries\\*MA_RFP -- v0.0.2.5\\GaN Product\\CGHV1F006S")
#it1_load_pull
#load_data_1:G_LPCM(PAE,0.5,12,50,0)[1,*]
#b=awr.graph.measurement.extract_contours(graph_name="it1_source_pull", measurement_name="source_data_1:G_LPCM(PAE,0.25,12,50,0)[1,*]" )
#b=awr.graph.measurement.extract_point_data(graph_name="it1_source_pull", measurement_name="source_data_1:G_LPCMMAX(PAE,50,0,0)[1,*]")

b = awr.graph.marker.get_marker_data(graph_title="it1_source_pull", marker_designator="m2", perform_simulation=False, toggle_enable=False)

print("hello")