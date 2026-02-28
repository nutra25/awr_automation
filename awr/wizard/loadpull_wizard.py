"""
loadpull_wizard.py
Provides atomic functionality to execute and configure the AWR Load Pull Wizard.
Strictly adheres to the tree-branch logging hierarchy.
"""

import pyawr.mwoffice as mwoffice
import time
import sys
from typing import Dict, Any

from logger.logger import LOGGER


def run_loadpull_wizard(app: Any, config_params: Dict[str, Any]) -> bool:
    """
    Executes the AWR Load Pull Wizard automation sequence.
    Connects to the active session, instantiates the wizard, applies parameters,
    and triggers the execution safely.

    Args:
        app: The active AWR MWOffice COM application instance.
        config_params (Dict[str, Any]): A dictionary mapping wizard parameter names to values.

    Returns:
        bool: True if the wizard executed successfully, False otherwise.
    """
    LOGGER.info("├── Initiating Load Pull Wizard Automation Sequence...")

    try:
        project = app.Project

        # Attempt to locate the wizard definition by name or its known GUID
        LOAD_PULL_GUID = "{85CA0552-53C3-404C-A0E9-3ECFF0D5D261}"
        target_wizard = None

        if project.Wizards.Exists("Load Pull Wizard"):
            target_wizard = project.Wizards.Item("Load Pull Wizard")
        elif project.Wizards.Exists(LOAD_PULL_GUID):
            target_wizard = project.Wizards.Item(LOAD_PULL_GUID)

        if not target_wizard:
            LOGGER.error("└── Load Pull Wizard definition not found in the AWR system.")
            return False

        LOGGER.debug("│   ├── Wizard definition located. Instantiating configuration...")

        # Create a new wizard instance and cast it to the specific LoadPull interface
        wizard_instance_disp = target_wizard.CreateNew()
        caster = project.Wizards.WizardCast
        lp_runner = caster.LoadPullWizard(wizard_instance_disp)

        LOGGER.info("│   ├── Configuring Wizard Parameters...")

        success_count = 0
        fail_count = 0

        # Convert items to a list to determine the loop end for visual tree formatting
        param_items = list(config_params.items())
        total_params = len(param_items)

        for index, (param_name, param_value) in enumerate(param_items):
            is_last = (index == total_params - 1)
            tree_char = "└──" if is_last else "├──"

            # Attempt to read the current value for logging purposes
            old_val_str = "?"
            try:
                current_val = lp_runner.GetOption(str(param_name))
                old_val_str = str(current_val)
            except Exception:
                old_val_str = "Unknown"

            # Attempt to set the new value
            try:
                if param_value is None:
                    LOGGER.debug(f"│   │   {tree_char} {param_name}: SKIPPED (None)")
                    continue

                lp_runner.PutOption(str(param_name), param_value)

                # Log the change in standard format: [Old] -> [New]
                LOGGER.info(f"│   │   {tree_char} {param_name}: [{old_val_str}] -> [{param_value}]")
                success_count += 1

            except Exception as opt_err:
                LOGGER.error(f"│   │   {tree_char} {param_name}: FAILED -> {opt_err}")
                fail_count += 1

        LOGGER.info(f"│   ├── Configuration Summary: {success_count} Success, {fail_count} Failed.")

        if success_count > 0:
            LOGGER.info("│   ├── Triggering Load Pull Execution (Exec)...")
            lp_runner.Exec()

            # Wait loop to ensure the simulation completes before proceeding
            LOGGER.debug("│   │   └── Waiting for simulation to finish...")
            while project.Simulator.AnalyzeState == 2:
                time.sleep(1)

            LOGGER.info("└── Load Pull Process Completed Successfully.")
            return True
        else:
            LOGGER.warning("└── Execution ABORTED: No parameters were successfully configured.")
            return False

    except Exception as e:
        LOGGER.error(f"└── Critical Error in Load Pull Wizard: {e}")
        return False


# Standalone Test Execution Block
if __name__ == "__main__":
    LOGGER.info("Starting standalone test sequence for loadpull_wizard.py")
    try:
        test_app = mwoffice.CMWOffice()
        LOGGER.info("├── Successfully connected to AWR Microwave Office for testing.")

        my_params = {
            "LP_MaxHarmonic": 1,
            "LP_DataFileName": "source_data_1",
            "LP_OverwriteDataFile": True,
            "LP_Sweep_Source1": True,
            "LP_Source1_Density": "Extra fine",
            "LP_Source1_Radius": 0.99,
        }

        run_loadpull_wizard(test_app, my_params)
    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed: {ex}")
        sys.exit(1)