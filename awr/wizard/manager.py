"""
manager.py (Wizard Domain)
Encapsulates API operations required to interact with integrated
AWR wizards, specifically the Load Pull sequence.
"""

from typing import Dict, Any
from awr.wizard.awr_loadpull_wizard import run_loadpull_wizard

class WizardManager:
    """
    Manages AWR Wizard automation interactions.
    """
    def __init__(self, app):
        self.app = app

    def run_wizard(self, options: Dict[str, Any]) -> None:
        """Triggers the Load Pull Wizard with a specified configuration dictionary."""
        run_loadpull_wizard(self.app, options)