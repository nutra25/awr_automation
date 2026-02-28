"""
manager.py (Wizard Domain)
Handles interactions with AWR automated wizards, templates, and global scripts.
Enforces domain encapsulation.
"""

from typing import Any, Dict

from awr.wizard.create_load_pull_template import create_load_pull_template
from awr.wizard.loadpull_wizard import run_loadpull_wizard


class WizardManager:
    """
    Manages AWR Wizard and Script automation sequences.
    """
    def __init__(self, app: Any):
        self.app = app

    def create_load_pull_template(self) -> bool:
        """
        Executes the 'Load Pull Template' script and automatically dismisses
        any associated blocking UI pop-ups.
        """
        return create_load_pull_template(self.app)

    def run_loadpull_wizard(self, config_params: Dict[str, Any]) -> bool:
        """
        Configures and executes the automated Load Pull Wizard using a specific parameter dictionary.
        """
        return run_loadpull_wizard(self.app, config_params)