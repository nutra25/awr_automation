import math
from typing import Dict, List, Any
from logger import LOGGER

def extract_graph_data(app_instance: Any, graph_name: str) -> Dict[float, List[Dict[str, Any]]]:
    """
    Executes the AWR Graph Data Extraction sequence
    
    This function connects to the active AWR session locates the specified graph
    iterates through its measurements and extracts PAE and Frequency data
    It parses trace values into contiguous islands of valid complex points
    The process is logged with a structured tree format to track status
    
    Args:
        app_instance (Any): The AWR application instance
        graph_name (str): The name of the graph to extract data from
        
    Returns:
        Dict[float, List[Dict[str, Any]]]: A dictionary grouping PAE and island data by frequency
        
    Raises:
        Exception: For any critical failures during data extraction
    """
    LOGGER.info(f"Starting Data Extraction Sequence for Graph: {graph_name}")
    
    try:
        project = app_instance.Project
        
        if not project.Graphs.Exists(graph_name):
            LOGGER.critical(f"  └─ Graph NOT found in AWR system: {graph_name}")
            return {}
            
        LOGGER.debug("  ├─ Graph located Instantiating data structures")
        
        graph = project.Graphs(graph_name)
        data_by_freq = {}

        try:
            # Simulation steps are logged as DEBUG to keep the console output clean
            LOGGER.debug("  ├── Starting Simulation (Analyze)...")
            simulator = project.Simulator
            simulator.Analyze()
            LOGGER.debug("  ├── Simulation Completed.")
        except Exception as sim_error:
            LOGGER.critical(f"  └─ Simulation FAILED: {sim_error}")
            raise RuntimeError(f"Simulation execution failed: {sim_error}")
        
        meas_items = list(graph.Measurements)
        total_meas = len(meas_items)
        
        LOGGER.info("  ├── Extracting Measurement Traces:")
        
        for m_idx, meas in enumerate(meas_items):
            is_last_meas = (m_idx == total_meas - 1)
            tree_char_m = "└──" if is_last_meas else "├──"
            
            if not meas.Enabled:
                LOGGER.debug(f"  │   {tree_char_m} Measurement {meas.Name}: SKIPPED (Disabled)")
                continue
                
            for i in range(1, meas.TraceCount + 1):
                try:
                    sweep_labels = meas.SweepLabels(i)
                    pae_val, freq_val = None, None
                    
                    if sweep_labels.Count > 0:
                        for label_idx in range(1, sweep_labels.Count + 1):
                            lbl = sweep_labels.Item(label_idx)
                            name_up = lbl.Name.upper()
                            if name_up == "PAE": 
                                pae_val = float(lbl.Value)
                            elif name_up in ["F1", "FREQ", "FREQUENCY"]: 
                                freq_val = float(lbl.Value)
                                
                    if pae_val is not None and freq_val is None:
                        freq_val = 0.0
                        
                    if pae_val is None:
                        continue
                        
                    data = meas.TraceValues(i)
                    if not data:
                        continue
                        
                    islands = []
                    curr_r, curr_i = [], []

                    if isinstance(data[0], (int, float)):
                        step = 3 if len(data) % 3 == 0 else 2
                        points = []
                        for k in range(0, len(data) - (step - 1), step):
                            if step == 3:
                                points.append((data[k], data[k+1], data[k+2]))
                            else:
                                points.append((0.0, data[k], data[k+1]))
                    else:
                        points = data
                        
                    for pt in points:
                        r, im = pt[1], pt[2]
                        is_valid = not (math.isnan(r) or math.isinf(r) or math.isnan(im) or math.isinf(im))
                        if is_valid and (abs(r) > 3.0 or abs(im) > 3.0):
                            is_valid = False
                            
                        if is_valid:
                            curr_r.append(r)
                            curr_i.append(im)
                        else:
                            if len(curr_r) > 2:
                                if curr_r[0] != curr_r[-1] or curr_i[0] != curr_i[-1]:
                                    curr_r.append(curr_r[0])
                                    curr_i.append(curr_i[0])
                                islands.append({'real': curr_r, 'imag': curr_i})
                            curr_r, curr_i = [], []
                            
                    if len(curr_r) > 2:
                        if curr_r[0] != curr_r[-1] or curr_i[0] != curr_i[-1]:
                            curr_r.append(curr_r[0])
                            curr_i.append(curr_i[0])
                        islands.append({'real': curr_r, 'imag': curr_i})
                        
                    if islands:
                        if freq_val not in data_by_freq:
                            data_by_freq[freq_val] = []
                        data_by_freq[freq_val].append({'pae': pae_val, 'islands': islands})
                        
                except Exception as e:
                    if i == 1:
                        LOGGER.error(f"  │   {tree_char_m} Trace #{i} read FAILED -> {e}")
                        
        LOGGER.info("  └── Data Extraction Process Completed Successfully")
        return data_by_freq
        
    except Exception as e:
        LOGGER.critical(f"  └─ Critical Error in Graph Data Extraction: {e}")
        raise