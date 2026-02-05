import pyawr.mwoffice as mwoffice

def get_marker_value(
        graph_title: str,
        marker_designator: str,
        perform_simulation: bool = True,
        toggle_enable: bool = False
) -> str:
    """
    Gets the raw data value text from a specific marker on a graph in AWR Microwave Office.

    This function connects to the active AWR session, optionally triggers a simulation,
    locates the specified graph and marker, and returns the marker's text value.

    Args:
        graph_title (str): The case-sensitive name of the graph containing the marker.
        marker_designator (str): The name of the marker (e.g., "m1").
        perform_simulation (bool): If True, triggers a simulation before reading the value.
                                   Defaults to True.

    Returns:
        str: The raw text string of the marker's value. Returns an empty string if the
             marker is found but has no value.

    Raises:
        RuntimeError: If the application session cannot be established, simulation fails, or the marker/graph is not found.
    """

    # 1. Initialize Application Session
    try:
        application_session = mwoffice.CMWOffice()
    except Exception as connection_exception:
        raise RuntimeError(f"Failed to initialize AWR Microwave Office session: {connection_exception}")

    # 2. Access Project
    project_reference = application_session.Project

    # 3. Get Target Graph
    target_graph = None
    # Iterate through graphs to find the matching name safely
    for graph in project_reference.Graphs:
        if graph.Name == graph_title:
            target_graph = graph
            break

    if target_graph is None:
        raise RuntimeError(f"The graph '{graph_title}' could not be located in the active project.")

    # Toggle Enable (Optional)
    if toggle_enable:
        for meas in target_graph.Measurements:
            # Durumu ayarla (True = Enable, False = Disable)
            # Kaynak: CMeasurement.Enabled [1]
            meas.Enabled = True
            print(f"{meas.Name} durumu: {meas.Enabled}")

    # 4. Perform Simulation (Optional)
    if perform_simulation:
        try:
            simulator = project_reference.Simulator
            # Check if simulation is needed or force analysis
            simulator.Analyze()
        except Exception as sim_error:
            raise RuntimeError(f"Simulation execution failed: {sim_error}")

    # 5. Locate the Marker
    target_marker = None
    target_designator_clean = marker_designator.strip().lower()

    for marker in target_graph.Markers:
        if marker.Name.strip().lower() == target_designator_clean:
            target_marker = marker
            break

    if target_marker is None:
        raise RuntimeError(f"Marker '{marker_designator}' was not found on graph '{graph_title}'.")

    # 6. Get Data Value
    try:
        # CMarker object provides the 'DataValueText' property
        raw_text = target_marker.DataValueText
        # Toggle Disable
        if toggle_enable:
            for meas in target_graph.Measurements:
                meas.Enabled = False
                print(f"{meas.Name} durumu: {meas.Enabled}")
        return str(raw_text) if raw_text is not None else ""
    except Exception as read_error:
        raise RuntimeError(f"Failed to read data from marker '{marker_designator}': {read_error}")

