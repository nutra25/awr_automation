import pyawr.mwoffice as mwoffice
from typing import Dict, Any
import time

def run_loadpull_wizard(config_params: Dict[str, Any]):
    """
    Runs the Load Pull Wizard automation.

    Now includes a debugging step to READ (GetOption) the current value/type
    before writing (PutOption) the new value.
    """
    try:
        app = mwoffice.CMWOffice()
        project = app.Project

        # 1. Find Load Pull Wizard Definition
        LOAD_PULL_GUID = "{85CA0552-53C3-404C-A0E9-3ECFF0D5D261}"
        target_wizard = None

        if project.Wizards.Exists("Load Pull Wizard"):
            target_wizard = project.Wizards.Item("Load Pull Wizard")
        elif project.Wizards.Exists(LOAD_PULL_GUID):
            target_wizard = project.Wizards.Item(LOAD_PULL_GUID)

        if not target_wizard:
            print("Error: Load Pull Wizard not found in the system.")
            return

        print("Wizard definition found. Creating a new configuration instance...")

        # 2. Create a New Wizard Instance (CreateNew)
        wizard_instance_disp = target_wizard.CreateNew()

        # 3. Cast to Interface via WizardCast
        caster = project.Wizards.WizardCast
        lp_runner = caster.LoadPullWizard(wizard_instance_disp)

        print("Automation object ready. Inspecting and setting parameters...\n")
        print(f"{'PARAMETER':<30} | {'CURRENT (AWR)':<25} | {'TYPE':<10} -> {'ACTION'}")
        print("-" * 90)

        # 4. Set Parameters via Loop (GetOption -> Print -> PutOption)
        success_count = 0
        fail_count = 0

        for param_name, param_value in config_params.items():
            param_str = str(param_name)

            # --- STEP A: INSPECT CURRENT VALUE (GetOption) ---
            try:
                # Try to read the parameter from AWR before changing it
                current_val = lp_runner.GetOption(param_str)
                current_type = type(current_val).__name__

                # Print formatted info
                print(f"{param_str:<30} | {str(current_val):<25} | {current_type:<10}", end=" -> ")

            except Exception:
                # Some parameters might be write-only or fail if not initialized
                print(f"{param_str:<30} | {'<READ FAILED>':<25} | {'?'}", end=" -> ")

            # --- STEP B: SET NEW VALUE (PutOption) ---
            try:
                if param_value is None:
                    print("SKIPPED (Value is None)")
                    continue

                lp_runner.PutOption(param_str, param_value)
                print(f"SET OK: {param_value}")
                success_count += 1

            except Exception as opt_err:
                print(f"ERROR: {opt_err}")
                fail_count += 1

        print("-" * 90)
        print(f"Configuration finished. (Success: {success_count}, Failed: {fail_count})")

        # 5. Execute (Exec)
        if success_count > 0:
            print("\nExecuting Exec() command...")
            lp_runner.Exec()
            while project.Simulator.AnalyzeState == 2:
                time.sleep(0.5)  # İşlemciyi yormamak için kısa bekleme
            print("Load Pull process triggered successfully.")
        else:
            print("\nExec canceled because no parameters were successfully set.")

    except Exception as e:
        print(f"Critical General Error: {e}")


if __name__ == "__main__":
    # Example usage
    my_params = {
        "LP_MaxHarmonic": 1,
        "LP_DataFileName": "source_data_1",
        "LP_OverwriteDataFile": True,
        "LP_Sweep_Source1": True,
        "LP_Sweep_Load1": False,
        "LP_Source1_Density": "Extra fine",
        "LP_Source1_Radius": float(0.99),
        "LP_Source1_CenterMagnitude": float(0.0),
        "LP_Source1_CenterAngle": float(0.0),
    }
    run_loadpull_wizard(my_params)