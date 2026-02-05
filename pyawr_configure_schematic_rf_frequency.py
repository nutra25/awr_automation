import pyawr.mwoffice as mwoffice
from typing import Union, List

def configure_schematic_rf_frequency(schematic_name: str, frequencies: Union[float, List[float]]):
    """
    Configures the RF frequencies for a specific schematic.

    Args:
        schematic_name (str): The name of the schematic in the project.
        frequencies (float | List[float]): A single frequency or a list of frequencies in GHz.
    """
    try:
        # Connect to AWR
        app = mwoffice.CMWOffice()
        project = app.Project

        # check if schematic exists
        if project.Schematics.Exists(schematic_name):
            schematic = project.Schematics(schematic_name)
            print(f"Schematic found: {schematic_name}")

            # Step 1: Disable "Use project defaults"
            # This is necessary to set local frequencies for this specific schematic.
            schematic.UseProjectFrequencies = False

            # Step 2: Clear existing frequencies
            # We want to ensure only the requested frequencies exist.
            schematic.Frequencies.Clear()

            # Ensure 'frequencies' is treated as a list even if a single float is passed
            if isinstance(frequencies, (int, float)):
                freq_list = [frequencies]
            else:
                freq_list = frequencies

            # Step 3: Add new frequencies
            print(f"Applying {len(freq_list)} frequency point(s)...")
            for freq in freq_list:
                schematic.Frequencies.Add(freq*1e9)
                print(f" -> Added: {freq} GHz")

            print("Configuration complete.")

        else:
            print(f"Error: Schematic '{schematic_name}' not found in the project.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Example 1: Set a single frequency
    print("--- Test 1: Single Frequency ---")
    configure_schematic_rf_frequency(
        schematic_name="VDS40_Load_Pull",
        frequencies=13
    )
    """
    # Example 2: Set multiple frequencies (List)
    print("\n--- Test 2: Multiple Frequencies ---")
    configure_schematic_rf_frequency(
        schematic_name="VDS40_Load_Pull",
        frequencies=[12.7, 12.8, 12.9]
    )"""