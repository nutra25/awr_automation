from typing import Union, List
from logger import LOGGER


def configure_schematic_rf_frequency(app_instance, schematic_name: str, frequencies: Union[float, List[float]]):
    """
    Configures the RF simulation frequencies for a specific AWR schematic.

    This function connects to the active project, disables project-wide frequency
    defaults for the target schematic, clears existing points, and applies the
    new frequency list. It supports both single float inputs and lists of floats.

    Args:
        schematic_name (str): The name of the schematic to configure.
        frequencies (Union[float, List[float]]): A single frequency or a list of
                                                 frequencies in GHz.

    Raises:
        ValueError: If the specified schematic is not found in the project.
        RuntimeError: If a critical error occurs during the AWR connection or configuration.
    """
    LOGGER.info(f"Configuring RF Frequencies: '{schematic_name}'")

    try:
        project = app_instance.Project

        if project.Schematics.Exists(schematic_name):
            schematic = project.Schematics(schematic_name)
            LOGGER.debug(f"  ├─ Connected to schematic: {schematic_name}")

            # Ensure the schematic uses local frequency settings instead of project defaults
            if schematic.UseProjectFrequencies:
                schematic.UseProjectFrequencies = False
                LOGGER.info(f"  ├── Project defaults disabled.")

            # Remove existing frequency points to ensure a clean configuration state
            old_count = schematic.Frequencies.Count
            schematic.Frequencies.Clear()
            LOGGER.debug(f"  ├─ Cleared {old_count} existing points.")

            # Normalize input: ensure frequencies are always processed as a list
            freq_list = [frequencies] if isinstance(frequencies, (int, float)) else frequencies
            total_freqs = len(freq_list)

            # Iterate through frequencies, converting GHz to Hz (AWR base unit)
            for i, freq in enumerate(freq_list):
                schematic.Frequencies.Add(freq * 1e9)

                # Determine visual tree structure (last item gets '└──')
                is_last = (i == total_freqs - 1)
                tree_char = "└──" if is_last else "├──"

                LOGGER.info(f"  {tree_char} Added Frequency: {freq} GHz")

        else:
            LOGGER.error(f"  └─ Schematic NOT found: '{schematic_name}'")
            raise ValueError(f"Schematic '{schematic_name}' is missing.")

    except Exception as e:
        LOGGER.critical(f"  └─ Critical error in frequency config: {e}")
        raise


if __name__ == "__main__":
    configure_schematic_rf_frequency(
        schematic_name="VDS40_Load_Pull",
        frequencies=[12.0, 13.0, 14.0]
    )