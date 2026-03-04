import math
from typing import List, Any, Optional
from core.logger import logger
from awr.graph.perform_simulation import perform_simulation


def extract_single_point_data(app_instance: Any, graph_name: str, measurement_name: str) -> Optional[List[Any]]:
    """
    Executes a generic data extraction sequence for a specified measurement.

    This function isolates the AWR extraction logic from the business logic.
    It triggers a simulation, locates the target graph and measurement using
    robust string matching, and returns the raw trace values while preserving
    their original nested or flat structure.

    Args:
        app_instance (Any): The active AWR MWOffice COM application instance.
        graph_name (str): The name of the target graph.
        measurement_name (str): The exact or partial name of the measurement to extract.

    Returns:
        Optional[List[Any]]: A list of raw extracted values (can contain nested tuples for multidimensional points), or None if extraction fails.
    """
    logger.info("Initiating Generic Data Extraction Sequence")
    logger.info(f"├── Target Graph: {graph_name}")
    logger.info(f"├── Target Measurement: {measurement_name}")

    try:
        project = app_instance.Project

        if not project.Graphs.Exists(graph_name):
            logger.error(f"└── Extraction Failed: Graph '{graph_name}' does not exist in the active project.")
            return None

        logger.debug("├── Target graph located. Executing simulation sequence.")
        perform_simulation(app_instance)

        graph = project.Graphs(graph_name)

        target_meas = None
        available_measurements = []

        target_clean = measurement_name.replace(" ", "").upper()

        for meas in graph.Measurements:
            meas_name = meas.Name
            available_measurements.append(meas_name)

            actual_clean = meas_name.replace(" ", "").upper()

            if target_clean in actual_clean or actual_clean in target_clean:
                target_meas = meas
                break

        if not target_meas:
            logger.error(
                f"└── Extraction Failed: Measurement '{measurement_name}' not found within graph '{graph_name}'.")
            logger.debug("    ├── Available measurements in this graph according to AWR COM:")

            for idx, am in enumerate(available_measurements):
                prefix = "└──" if idx == len(available_measurements) - 1 else "├──"
                logger.debug(f"    │   {prefix} '{am}'")

            return None

        if not target_meas.Enabled:
            logger.warning(f"└── Extraction Aborted: Measurement '{target_meas.Name}' is currently disabled.")
            return None

        logger.debug(f"├── Target measurement verified as: '{target_meas.Name}'. Fetching raw trace values.")

        try:
            # Extract raw trace data directly from the COM interface
            raw_data = target_meas.TraceValues(1)

            if not raw_data:
                logger.error("└── Extraction Failed: Retrieved trace data is empty.")
                return None

            # Convert the COM object to a standard Python list, preserving any nested tuples
            data_list = list(raw_data)

            logger.info(
                f"└── Data extraction completed successfully. Retrieved {len(data_list)} primary data elements.")
            return data_list

        except Exception as e:
            logger.error(f"└── Trace read operation failed for measurement '{target_meas.Name}': {e}")
            return None

    except Exception as e:
        logger.error(f"└── Critical framework error during data extraction: {e}")
        return None