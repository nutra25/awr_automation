from logger.logger import LOGGER


def get_marker_value(
        app_instance,
        graph_title: str,
        marker_designator: str,
        perform_simulation: bool = True,
        toggle_enable: bool = False
) -> str:
    """
    Retrieves the data value from a specific marker on a graph in AWR Microwave Office.

    This function connects to the active project, locates the specified graph and marker,
    and optionally runs a simulation to ensure data is up-to-date. The process is logged
    using a structured tree format.

    Args:
        graph_title (str): The name of the graph containing the marker.
        marker_designator (str): The name or ID of the marker to read (e.g., 'm1').
        perform_simulation (bool): If True, triggers a simulation analysis before reading.
        toggle_enable (bool): If True, temporarily enables measurements for this graph
                              before simulation and disables them afterwards.

    Returns:
        str: The raw text value of the marker. Returns an empty string if reading fails.

    Raises:
        RuntimeError: If AWR connection fails, the graph/marker is missing, or simulation fails.
    """
    LOGGER.info(f"Retrieving Marker Data: '{marker_designator}' from '{graph_title}'")

    try:
        application_session = app_instance
    except Exception as connection_exception:
        LOGGER.critical(f"  └─ Failed to connect to AWR: {connection_exception}")
        raise RuntimeError(f"AWR Session Initialization Error: {connection_exception}")

    project_reference = application_session.Project
    LOGGER.debug(f"  ├─ Connected to active project.")

    target_graph = None
    for graph in project_reference.Graphs:
        if graph.Name == graph_title:
            target_graph = graph
            break

    if target_graph is None:
        LOGGER.error(f"  └─ Graph NOT found: '{graph_title}'")
        raise RuntimeError(f"Graph '{graph_title}' not found.")

    LOGGER.debug(f"  ├─ Graph located: {target_graph.Name}")

    # Optionally enable measurements for this graph to ensure they are calculated during simulation
    if toggle_enable:
        LOGGER.debug(f"  ├─ Enabling measurements for graph...")
        for meas in target_graph.Measurements:
            meas.Enabled = True

    if perform_simulation:
        try:
            # Simulation steps are logged as DEBUG to keep the console output clean
            LOGGER.debug("  ├── Starting Simulation (Analyze)...")
            simulator = project_reference.Simulator
            simulator.Analyze()
            LOGGER.debug("  ├── Simulation Completed.")
        except Exception as sim_error:
            LOGGER.critical(f"  └─ Simulation FAILED: {sim_error}")
            raise RuntimeError(f"Simulation execution failed: {sim_error}")
    else:
        LOGGER.debug(f"  ├─ Simulation skipped (perform_simulation=False).")

    # Locate the marker using case-insensitive matching
    target_marker = None
    target_designator_clean = marker_designator.strip().lower()

    for marker in target_graph.Markers:
        if marker.Name.strip().lower() == target_designator_clean:
            target_marker = marker
            break

    if target_marker is None:
        LOGGER.error(f"  └─ Marker '{marker_designator}' NOT found on graph.")
        raise RuntimeError(f"Marker '{marker_designator}' missing.")

    try:
        raw_text = target_marker.DataValueText

        # Revert measurement enablement if it was toggled on earlier
        if toggle_enable:
            LOGGER.debug(f"  ├─ Disabling measurements...")
            for meas in target_graph.Measurements:
                meas.Enabled = False

        if raw_text:
            LOGGER.info(f"  └── Value: {raw_text}")
        else:
            LOGGER.warning(f"  └── Marker value is empty.")

        return str(raw_text) if raw_text is not None else ""

    except Exception as read_error:
        LOGGER.error(f"  └─ Error reading marker data: {read_error}")
        raise RuntimeError(f"Failed to read data: {read_error}")