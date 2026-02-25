"""
lp_tuner_utils.py
Provides utility functions and enumerations for tuner configurations.
Designed to be completely configuration-agnostic; requires explicit settings injection.
"""

from typing import Any, Dict
from enum import Enum, auto


class PullType(Enum):
    """Enumeration defining the active impedance pull direction."""
    LOADPULL = auto()
    SOURCEPULL = auto()


def build_tuner_params(tuner_settings: Dict[str, Any], side: str, mag: Any, ang: Any, harmonic: int = 1) -> dict:
    """
    Formats tuner parameters for the AWR environment based on injected settings.

    Args:
        tuner_settings: The dictionary containing prefix configurations.
        side: Target side, typically 'SOURCE' or 'LOAD'.
        mag: Magnitude value to set.
        ang: Angle value to set.
        harmonic: Target harmonic index. Defaults to 1.

    Returns:
        A dictionary formatted for the circuit manager.
    """
    cfg = tuner_settings[side]
    return {
        f"{cfg['prefix_mag']}{harmonic}": str(mag),
        f"{cfg['prefix_ang']}{harmonic}": str(ang)
    }