"""
models.py
Defines the domain data structures for Load-Pull operations.
"""
from dataclasses import dataclass

@dataclass
class PullResult:
    """Records the absolute metrics extracted from a specific load/source pull iteration."""
    iter_no: int
    mode: str  # "SP" (Source Pull) or "LP" (Load Pull)
    point: str
    mag: float
    ang: float