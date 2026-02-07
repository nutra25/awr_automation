import pyawr.mwoffice as mwoffice
from typing import Dict, Any
import time
from logger import LOGGER


def run_loadpull_wizard(config_params: Dict[str, Any]):
    """
    Executes the AWR Load Pull Wizard automation sequence.

    This function connects to the active AWR session, identifies the Load Pull Wizard
    (by name or GUID), applies the provided configuration parameters, and triggers
    the simulation execution. The process is logged with a structured tree format
    to track parameter changes and status.

    Args:
        config_params (Dict[str, Any]): A dictionary where keys are the wizard
                                        parameter names (e.g., 'LP_MaxHarmonic')
                                        and values are the settings to apply.

    Raises:
        RuntimeError: If the AWR session fails to initialize.
        ValueError: If the Load Pull Wizard definition cannot be found in the project.
        Exception: For any critical failures during parameter setting or execution.
    """
    LOGGER.info("Starting Load Pull Wizard Automation Sequence")

    try:
        app = mwoffice.CMWOffice()
        project = app.Project

        # Attempt to locate the wizard definition by name or its known GUID
        LOAD_PULL_GUID = "{85CA0552-53C3-404C-A0E9-3ECFF0D5D261}"
        target_wizard = None

        if project.Wizards.Exists("Load Pull Wizard"):
            target_wizard = project.Wizards.Item("Load Pull Wizard")
        elif project.Wizards.Exists(LOAD_PULL_GUID):
            target_wizard = project.Wizards.Item(LOAD_PULL_GUID)

        if not target_wizard:
            LOGGER.critical("  └─ Load Pull Wizard definition NOT found in AWR system.")
            return

        LOGGER.debug("  ├─ Wizard definition located. Instantiating configuration...")

        # Create a new wizard instance and cast it to the specific LoadPull interface
        wizard_instance_disp = target_wizard.CreateNew()
        caster = project.Wizards.WizardCast
        lp_runner = caster.LoadPullWizard(wizard_instance_disp)

        LOGGER.info("  ├── Configuring Wizard Parameters:")

        success_count = 0
        fail_count = 0

        # Convert items to a list to determine the loop end for visual tree formatting
        param_items = list(config_params.items())
        total_params = len(param_items)

        for index, (param_name, param_value) in enumerate(param_items):
            # Determine tree branch character based on list position
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
                    LOGGER.debug(f"    {tree_char} {param_name}: SKIPPED (None)")
                    continue

                lp_runner.PutOption(str(param_name), param_value)

                # Log the change in standard format: [Old] -> [New]
                LOGGER.info(f"    {tree_char} {param_name}: [{old_val_str}] -> [{param_value}]")
                success_count += 1

            except Exception as opt_err:
                LOGGER.error(f"    {tree_char} {param_name}: FAILED -> {opt_err}")
                fail_count += 1

        LOGGER.info(f"  ├── Configuration Summary: {success_count} Success, {fail_count} Failed.")

        if success_count > 0:
            LOGGER.info("  ├── Triggering Load Pull Execution (Exec)...")
            lp_runner.Exec()

            # Wait loop to ensure the simulation completes before proceeding
            # Logging is silenced inside the loop to prevent console spam
            LOGGER.debug("  │   Waiting for simulation to finish...")

            while project.Simulator.AnalyzeState == 2:
                time.sleep(1)

            LOGGER.info("  └── Load Pull Process Completed Successfully.")
        else:
            LOGGER.warning("  └── Execution ABORTED: No parameters were configured.")

    except Exception as e:
        LOGGER.critical(f"  └─ Critical Error in Load Pull Wizard: {e}")
        raise


if __name__ == "__main__":
    my_params = {
        "LP_MaxHarmonic": 1,
        "LP_DataFileName": "source_data_1",
        "LP_OverwriteDataFile": True,
        "LP_Sweep_Source1": True,
        "LP_Source1_Density": "Extra fine",
        "LP_Source1_Radius": 0.99,
    }
    run_loadpull_wizard(my_params)