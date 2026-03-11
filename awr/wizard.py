import time
from typing import Any, Dict

from awr.awr_component import AWRComponent


class Wizard(AWRComponent):

    def create_load_pull_template(self, timeout: float = 30.0) -> bool:
        """
        Executes the 'Create_Load_Pull_Template' routine directly and waits for the
        corresponding schematic to be generated within the given timeout limit.
        """
        self.logger.info("├── Initiating 'Load Pull Template' generation...")

        module_name = "Load_Pull"
        routine_name = "Create_Load_Pull_Template"

        try:
            self.logger.info(f"│   ├── Executing routine '{module_name}.{routine_name}' directly...")

            target_routine = self.app.GlobalScripts(module_name).Routines(routine_name)
            target_routine.Run()

            self.logger.debug("│   ├── Waiting for physical generation of the schematic...")

            start_wait = time.time()
            schematic_ready = False
            schematic_name = "Load_Pull_Template"

            while (time.time() - start_wait) < timeout:
                try:
                    if self.app.Project.Schematics.Exists(schematic_name):
                        schematic_ready = True
                        break
                except Exception:
                    pass
                time.sleep(0.5)

            if schematic_ready:
                self.logger.info("└── Load-Pull schematic template generated successfully.")
                return True
            else:
                self.logger.error("└── Sequence aborted: Timeout reached before schematic was generated.")
                return False

        except Exception as e:
            self.logger.error(
                f"└── Failed to execute Load-Pull template script '{module_name}.{routine_name}'. Details: {e}")
            return False

    def run_loadpull_wizard(self, config_params: Dict[str, Any]) -> bool:

        self.logger.info("├── Initiating Load Pull Wizard Automation Sequence...")

        try:
            project = self.app.Project

            LOAD_PULL_GUID = "{85CA0552-53C3-404C-A0E9-3ECFF0D5D261}"
            target_wizard = None

            if project.Wizards.Exists("Load Pull Wizard"):
                target_wizard = project.Wizards.Item("Load Pull Wizard")
            elif project.Wizards.Exists(LOAD_PULL_GUID):
                target_wizard = project.Wizards.Item(LOAD_PULL_GUID)

            if not target_wizard:
                self.logger.error("└── Load Pull Wizard definition not found in the AWR system.")
                return False

            self.logger.debug("│   ├── Wizard definition located. Instantiating configuration...")

            wizard_instance_disp = target_wizard.CreateNew()
            caster = project.Wizards.WizardCast
            lp_runner = caster.LoadPullWizard(wizard_instance_disp)

            self.logger.info("│   ├── Configuring Wizard Parameters...")

            success_count = 0
            fail_count = 0

            param_items = list(config_params.items())
            total_params = len(param_items)

            for index, (param_name, param_value) in enumerate(param_items):
                is_last = (index == total_params - 1)
                tree_char = "└──" if is_last else "├──"

                old_val_str = "?"
                try:
                    current_val = lp_runner.GetOption(str(param_name))
                    old_val_str = str(current_val)
                except Exception:
                    old_val_str = "Unknown"

                try:
                    if param_value is None:
                        self.logger.debug(f"│   │   {tree_char} {param_name}: SKIPPED (None)")
                        continue

                    lp_runner.PutOption(str(param_name), param_value)

                    self.logger.info(f"│   │   {tree_char} {param_name}: [{old_val_str}] -> [{param_value}]")
                    success_count += 1

                except Exception as opt_err:
                    self.logger.error(f"│   │   {tree_char} {param_name}: FAILED -> {opt_err}")
                    fail_count += 1

            self.logger.info(f"│   ├── Configuration Summary: {success_count} Success, {fail_count} Failed.")

            if success_count > 0:
                self.logger.info("│   ├── Triggering Load Pull Execution (Exec)...")
                lp_runner.Exec()

                self.logger.debug("│   │   └── Waiting for simulation to finish...")
                while project.Simulator.AnalyzeState == 2:
                    time.sleep(1)

                self.logger.info("└── Load Pull Process Completed Successfully.")
                return True
            else:
                self.logger.warning("└── Execution ABORTED: No parameters were successfully configured.")
                return False

        except Exception as e:
            self.logger.error(f"└── Critical Error in Load Pull Wizard: {e}")
            return False