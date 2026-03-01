"""
utils.py
Provides utility functions for engine operations.
Strictly acts as a helper module decoupled from domain models.
"""
import math
from decimal import Decimal
from typing import Tuple, Optional, Any


def normalize_to_tuple(x: Any) -> Tuple[str, ...]:
    """Converts the provided input into a uniform tuple of strings."""
    if isinstance(x, (list, tuple)):
        return tuple(str(v) for v in x)
    return (str(x),)


def _auto_decimals(*nums: float) -> int:
    def dec_places(x: float) -> int:
        d = Decimal(str(x)).normalize()
        exp = d.as_tuple().exponent
        return max(0, -exp)
    return max(dec_places(n) for n in nums)


def generate_sweep_values(
        start: float,
        stop: float,
        step: float,
        decimals: Optional[int] = None
) -> Tuple[str, ...]:
    """Generates a sequence of formatted string values for sweeping."""
    if step == 0:
        raise ValueError("Sweep step magnitude cannot be zero.")

    if decimals is None:
        decimals = _auto_decimals(start, stop, step)

    if start < stop and step < 0:
        step = abs(step)
    elif start > stop and step > 0:
        step = -abs(step)

    count = int(math.floor((stop - start) / step))
    values = [f"{(start + i * step):.{decimals}f}" for i in range(abs(count) + 1)]

    if values[-1] != f"{stop:.{decimals}f}":
        values.append(f"{stop:.{decimals}f}")

    return tuple(values)