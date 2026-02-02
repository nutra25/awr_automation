import pyawr.mwoffice as mwoffice

def configure_schematic_element(
        schematic_title: str,
        target_designator: str,
        parameter_map: dict[str, str],
        allow_partial_match: bool = False
) -> dict:
    """
    Locates a specific element within an AWR Microwave Office schematic and applies
    a set of parameter configurations.

    This function establishes a connection to the active application session, navigates
    the project hierarchy to the specified schematic, identifies the target component
    by name or ID, and updates the requested parameter values.

    Args:
        schematic_title (str): The case-sensitive name of the schematic containing the element.
        target_designator (str): The unique identifier (Name or ID) of the element to be modified.
        parameter_map (dict[str, str]): A dictionary where keys represent parameter names
                                        and values represent the desired settings (e.g., {"R": "50", "W": "100um"}).
        allow_partial_match (bool): If set to True, the function matches elements containing
                                    the target_designator string. If False, an exact match is required.
                                    Defaults to False.

    Returns:
        dict: A report structure containing the schematic name, the resolved element name,
              and a dictionary of successfully applied parameters.

    Raises:
        RuntimeError: If the application session cannot be established or the element is not found.
        ValueError: If the specified schematic does not exist in the current project.
    """

    # 1. Initialize Application Session
    # Establishes a connection to the COM object via the CMWOffice wrapper.
    try:
        application_session = mwoffice.CMWOffice()
    except Exception as connection_exception:
        raise RuntimeError(f"Failed to initialize AWR Microwave Office session: {connection_exception}")

    # 2. Retrieve Target Schematic
    # Accesses the Project object and the Schematics collection.
    try:
        project_reference = application_session.Project
        active_schematic = project_reference.Schematics(schematic_title)
    except Exception:
        raise ValueError(f"The schematic '{schematic_title}' could not be located within the active project.")

    identified_element = None

    # 3. Iterate Elements Collection to Identify Target
    # The Elements property returns a CElements collection, which allows iteration.
    for candidate_element in active_schematic.Elements:

        # Access the element's Name property.
        element_identifier = candidate_element.Name
        is_match = False

        # Verify against Designator (Name)
        if allow_partial_match:
            if target_designator in element_identifier:
                is_match = True
        else:
            if target_designator == element_identifier:
                is_match = True

        # Verify against ID Parameter (Secondary Identification)
        # Checks if the "ID" parameter exists in the CParameters collection.
        if not is_match and candidate_element.Parameters.Exists("ID"):
            # Retrieves the string representation of the ID value.
            element_id_value = candidate_element.Parameters("ID").ValueAsString
            if element_id_value == target_designator:
                is_match = True

        if is_match:
            identified_element = candidate_element
            break

    if identified_element is None:
        raise RuntimeError(
            f"No element matching designator '{target_designator}' was found in schematic '{schematic_title}'.")

    # 4. Apply Configuration Map
    configuration_report = {}

    for parameter_key, parameter_value in parameter_map.items():
        # Access the Parameters collection on the CElement object.
        if identified_element.Parameters.Exists(parameter_key):
            target_parameter = identified_element.Parameters(parameter_key)

            # Assign the value as a string to ensure proper unit handling by the API.
            target_parameter.ValueAsString = str(parameter_value)

            # Record the value actually set by the application for verification.
            configuration_report[parameter_key] = target_parameter.ValueAsString

    return {
        "schematic_source": active_schematic.Name,
        "element_identifier": identified_element.Name,
        "applied_configurations": configuration_report
    }
