"""
tuner_utils.py
Provides utility functions and enumerations for tuner configurations.
Replaces unstructured dictionaries with strongly typed configuration dataclasses.
"""

from typing import Any
from enum import Enum, auto
from dataclasses import dataclass, field


class PullType(Enum):
    """Enumeration defining the active impedance pull direction."""
    LOADPULL = auto()
    SOURCEPULL = auto()


@dataclass
class TunerSideConfig:
    """Configuration node for a specific tuner side (Source or Load)."""
    name: str
    prefix_mag: str
    prefix_ang: str
    harmonics_to_track: list = field(default_factory=lambda: [1])


@dataclass
class TunerConfig:
    """Master configuration node for the tuning system."""
    source: TunerSideConfig
    load: TunerSideConfig


def build_tuner_params(config: TunerConfig, side: str, mag: Any, ang: Any, harmonic: int = 1) -> dict:
    """
    Formats tuner parameters for the AWR environment based on injected strongly-typed settings.

    Args:
        config: The structured TunerConfig object containing prefix configurations.
        side: Target side, typically 'SOURCE' or 'LOAD'.
        mag: Magnitude value to set.
        ang: Angle value to set.
        harmonic: Target harmonic index. Defaults to 1.

    Returns:
        A dictionary formatted for the circuit manager.
    """
    cfg = config.source if side.upper() == "SOURCE" else config.load
    return {
        f"{cfg.prefix_mag}{harmonic}": str(mag),
        f"{cfg.prefix_ang}{harmonic}": str(ang)
    }