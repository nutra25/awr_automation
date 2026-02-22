from logger.logger import LOGGER


def configure_schematic_element(
        app_instance,
        schematic_title: str,
        target_designator: str,
        parameter_map: dict[str, str],
        allow_partial_match: bool = False
) -> dict:
    """
    Configures specific parameters of a target element within an AWR Microwave Office schematic.

    This function locates a schematic and an element (by Name or ID), then updates
    the specified parameters. It logs the process using a tree-structured format
    for readability.

    Args:
        schematic_title (str): The name of the schematic in the project.
        target_designator (str): The Name or ID of the element to configure.
        parameter_map (dict): A dictionary mapping parameter names to their new values.
        allow_partial_match (bool): If True, allows matching elements where the
                                    identifier is a substring of the element name.

    Returns:
        dict: A summary report containing the schematic name, element identifier,
              and the updated parameters.

    Raises:
        RuntimeError: If the AWR session cannot start or the element is not found.
        ValueError: If the specified schematic does not exist.
    """
    LOGGER.info(f"Configuring Element: '{target_designator}' in '{schematic_title}'")

    try:
        application_session = app_instance
    except Exception as connection_exception:
        LOGGER.critical(f"Failed to initialize AWR Microwave Office session: {connection_exception}")
        raise RuntimeError(f"Failed to initialize AWR Microwave Office session: {connection_exception}")

    try:
        project_reference = application_session.Project
        active_schematic = project_reference.Schematics(schematic_title)
        LOGGER.debug(f"  ├─ Schematic connection established: {active_schematic.Name}")
    except Exception:
        LOGGER.error(f"  └─ Schematic not found: '{schematic_title}'")
        raise ValueError(f"The schematic '{schematic_title}' could not be located within the active project.")

    identified_element = None

    # Iterate through all elements to find a match based on Name or ID
    for candidate_element in active_schematic.Elements:
        element_identifier = candidate_element.Name
        is_match = False

        if allow_partial_match:
            if target_designator in element_identifier:
                is_match = True
        else:
            if target_designator == element_identifier:
                is_match = True

        # If name match fails, attempt to match via the 'ID' parameter
        if not is_match and candidate_element.Parameters.Exists("ID"):
            element_id_value = candidate_element.Parameters("ID").ValueAsString
            if element_id_value == target_designator:
                is_match = True

        if is_match:
            identified_element = candidate_element
            LOGGER.debug(f"  ├─ Element matched by identifier: {identified_element.Name}")
            break

    if identified_element is None:
        LOGGER.warning(f"  └─ Element NOT found: {target_designator}")
        raise RuntimeError(
            f"No element matching designator '{target_designator}' was found in schematic '{schematic_title}'.")

    configuration_report = {}

    # Convert items to a list to determine the last iteration for logging formatting
    param_items = list(parameter_map.items())
    total_params = len(param_items)

    for index, (parameter_key, parameter_value) in enumerate(param_items):
        if identified_element.Parameters.Exists(parameter_key):
            target_parameter = identified_element.Parameters(parameter_key)
            old_value = target_parameter.ValueAsString

            # Update the parameter value in the schematic
            target_parameter.ValueAsString = str(parameter_value)
            configuration_report[parameter_key] = target_parameter.ValueAsString

            # Determine tree character based on loop position
            is_last_item = (index == total_params - 1)
            tree_char = "└──" if is_last_item else "├──"

            LOGGER.info(f"  {tree_char} {parameter_key}: [{old_value}] -> [{parameter_value}]")

        else:
            LOGGER.warning(f"  ├── Parameter '{parameter_key}' missing on element.")

    if not configuration_report:
        LOGGER.info(f"  └─ No parameters were updated.")

    return {
        "schematic_source": active_schematic.Name,
        "element_identifier": identified_element.Name,
        "applied_configurations": configuration_report
    }