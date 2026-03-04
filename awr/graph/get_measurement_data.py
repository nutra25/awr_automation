import math
import pyawr.mwoffice as mwoffice

from core.logger import logger

def extract_single_point_data(app, graph_name: str, measurement_name: str):
    """
    Locates the specified measurement within the given graph and retrieves
    all Y-dimension values associated with the first X-data point.
    """
    logger.info(f"├── Attempting to extract data from graph: '{graph_name}'")

    try:
        graph = app.Project.Graphs.Item(graph_name)
        logger.info("│   ├── Graph accessed successfully.")

        target_meas = None
        for i in range(1, graph.Measurements.Count + 1):
            meas = graph.Measurements.Item(i)
            if measurement_name in meas.Name:
                target_meas = meas
                logger.info(f"│   ├── Measurement match found: '{meas.Name}'")
                break

        if target_meas is None:
            logger.error(f"│   └── Measurement containing '{measurement_name}' not found.")
            return None, None

        if target_meas.XPointCount < 1:
            logger.error("│   └── Measurement contains no data points. Simulation may have failed.")
            return None, None

        single_x_val = target_meas.XValue(1)
        y_dimensions = target_meas.YDataDim

        logger.info(f"│   ├── Extracting data for single point (X = {single_x_val})")

        all_y_values = []
        for dim in range(1, y_dimensions + 1):
            y_val = target_meas.YValue(1, dim)
            all_y_values.append(y_val)

            # Dynamically determine the branch character for the tree structure
            branch_char = "└──" if dim == y_dimensions else "├──"
            logger.debug(f"│   │   {branch_char} Data dimension [{dim}] -> Y Value: {y_val}")

        logger.info("│   └── Data extraction completed successfully.")
        return single_x_val, all_y_values

    except Exception as e:
            logger.error(f"│   └── An error occurred during data extraction: {e}")
            return None, None


if __name__ == "__main__":
    logger.info("├── AWR Automation Script Initialized")

    try:
        app = mwoffice.CMWOffice()
        logger.info("│   ├── Connected to AWR Microwave Office.")
    except Exception as e:
        logger.critical(f"│   └── Failed to connect to AWR: {e}")
        exit(1)

    # Define target graph and measurement
    graph_target = "it1_load_pull"
    meas_target = "G_LPCMMAX(PAE"

    x_val, y_data = extract_single_point_data(app, graph_target, meas_target)

    # Validate data length before accessing indices to prevent IndexError
    if y_data and len(y_data) >= 3:
        max_pae = y_data[0]
        gamma_real = y_data[1]
        gamma_imag = y_data[2]

        # Calculate Magnitude and Angle
        gamma_mag = math.hypot(gamma_real, gamma_imag)
        gamma_ang = math.degrees(math.atan2(gamma_imag, gamma_real))

        logger.info("│   ├── Load-Pull Calculation Results:")
        logger.info(f"│   │   ├── Maximum PAE: {max_pae:.4f}")
        logger.info(f"│   │   ├── Optimum Tuner Gamma Magnitude: {gamma_mag:.4f}")
        logger.info(f"│   │   └── Optimum Tuner Gamma Angle: {gamma_ang:.2f} deg")
        logger.info("└── Execution finished successfully.")
    else:
        logger.error("└── Insufficient or missing data retrieved for calculations.")