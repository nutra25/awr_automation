"""
add_wire.py
Provides atomic functionality to draw physical electrical wires between coordinates.
Implements advanced obstacle and channel-aware routing to prevent both
accidental pin connections and unsightly wire overlapping (collinear overlap).
Strictly adheres to the tree-branch logging hierarchy.
"""

import pyawr.mwoffice as mwoffice
import sys
from typing import Any, List, Tuple, Set

from logger.logger import LOGGER

def get_schematic_obstacles(schematic: Any, exclude_points: List[Tuple[float, float]]) -> Tuple[Set[Tuple[float, float]], List[Tuple[float, float, float, float]]]:
    """Scans the schematic to map all pins (points) and existing wires (line segments)."""
    pins = set()
    wires = []

    # Extract all node/pin coordinates
    for elem in schematic.Elements:
        for node in elem.Nodes:
            pins.add((node.x, node.y))

    # Remove the starting and ending points of our current wire to prevent self-blocking
    for point in exclude_points:
        pins.discard(point)

    # Extract all existing wire segments
    for wire in schematic.Wires:
        wires.append((wire.x1, wire.y1, wire.x2, wire.y2))

    return pins, wires

def is_segment_collinear_overlap(sx1: float, sy1: float, sx2: float, sy2: float,
                                 wx1: float, wy1: float, wx2: float, wy2: float) -> bool:
    """Checks if two line segments overlap collinearly (run over each other)."""
    # Vertical Overlap Check
    if sx1 == sx2 and wx1 == wx2 and sx1 == wx1:
        min_s, max_s = min(sy1, sy2), max(sy1, sy2)
        min_w, max_w = min(wy1, wy2), max(wy1, wy2)
        # Strict inequality ensures that touching endpoints (like T-junctions) are allowed
        if max(min_s, min_w) < min(max_s, max_w):
            return True

    # Horizontal Overlap Check
    elif sy1 == sy2 and wy1 == wy2 and sy1 == wy1:
        min_s, max_s = min(sx1, sx2), max(sx1, sx2)
        min_w, max_w = min(wx1, wx2), max(wx1, wx2)
        if max(min_s, min_w) < min(max_s, max_w):
            return True

    return False

def is_path_clear(path: List[Tuple[float, float]],
                  pins: Set[Tuple[float, float]],
                  wires: List[Tuple[float, float, float, float]]) -> bool:
    """Checks if a path intersects unintended pins or completely overlaps existing wires."""
    for i in range(len(path) - 1):
        sx, sy = path[i]
        ex, ey = path[i+1]

        # 1. Pin Collision Check
        for (ox, oy) in pins:
            if sx == ex == ox:
                if min(sy, ey) <= oy <= max(sy, ey):
                    return False
            elif sy == ey == oy:
                if min(sx, ex) <= ox <= max(sx, ex):
                    return False

        # 2. Wire Channel (Collinear Overlap) Check
        for (wx1, wy1, wx2, wy2) in wires:
            if is_segment_collinear_overlap(sx, sy, ex, ey, wx1, wy1, wx2, wy2):
                return False

    return True

def generate_routing_candidates(x1: float, y1: float, x2: float, y2: float) -> List[List[Tuple[float, float]]]:
    """Generates an extensive prioritized list of orthogonal routing paths."""
    paths = []

    # 1. Straight Line Checks and their Offsets
    if x1 == x2 or y1 == y2:
        paths.append([(x1, y1), (x2, y2)])
        for offset in [100, -100, 200, -200, 300, -300]:
            if x1 == x2:
                paths.append([(x1, y1), (x1 + offset, y1), (x2 + offset, y2), (x2, y2)])
            else:
                paths.append([(x1, y1), (x1, y1 + offset), (x2, y1 + offset), (x2, y2)])
        return paths

    # 2. Standard L-Shapes
    paths.append([(x1, y1), (x2, y1), (x2, y2)]) # Horizontal -> Vertical
    paths.append([(x1, y1), (x1, y2), (x2, y2)]) # Vertical -> Horizontal

    # 3. Z-Shapes and advanced U-Shapes for channel routing (Bypassing wire overlaps)
    for offset in [100, -100, 200, -200, 300, -300, 400, -400]:
        paths.append([(x1, y1), (x1 + offset, y1), (x1 + offset, y2), (x2, y2)])
        paths.append([(x1, y1), (x1, y1 + offset), (x2, y1 + offset), (x2, y2)])
        paths.append([(x1, y1), (x2 + offset, y1), (x2 + offset, y2), (x2, y2)])
        paths.append([(x1, y1), (x1, y2 + offset), (x2, y2 + offset), (x2, y2)])

    return paths

def add_wire(app: Any, schematic_name: str, x1: float, y1: float, x2: float, y2: float) -> bool:
    """
    Draws a smart wire between two distinct coordinate points in the target schematic.
    It actively scans for other pins and existing wires to avoid short-circuits and visual overlaps.
    """
    try:
        schematic = app.Project.Schematics(schematic_name)

        # 1. Extract comprehensive obstacle mapping
        pins, wires = get_schematic_obstacles(schematic, exclude_points=[(x1, y1), (x2, y2)])

        # 2. Generate routing candidates
        candidate_paths = generate_routing_candidates(x1, y1, x2, y2)

        # 3. Evaluate and select the first strictly clear path
        best_path = None
        for idx, path in enumerate(candidate_paths):
            if is_path_clear(path, pins, wires):
                best_path = path
                if idx > 1:
                    LOGGER.debug(f"│   ├── Route adjusted to candidate {idx+1} to avoid channel overlap.")
                break

        # Fallback procedure: If extreme congestion exists, force the most direct route
        if not best_path:
            LOGGER.warning(f"│   ├── Congested area detected. Forcing standard overlap route to preserve connectivity.")
            best_path = candidate_paths[0]

        # 4. Instantiate the physical wire segments
        for i in range(len(best_path) - 1):
            px1, py1 = best_path[i]
            px2, py2 = best_path[i+1]
            if (px1 != px2) or (py1 != py2):
                schematic.Wires.Add(px1, py1, px2, py2)

        LOGGER.debug(f"│   ├── Drawn smart channel-aware wire with {len(best_path)-1} segment(s).")
        return True

    except Exception as e:
        LOGGER.error(f"│   ├── Failed to draw wire from ({x1}, {y1}) to ({x2}, {y2}). Details: {e}")
        return False


if __name__ == "__main__":
    LOGGER.info("Starting standalone test sequence for add_wire.py")
    try:
        test_app = mwoffice.CMWOffice()
        add_wire(test_app, "Load_Pull_Template", 0, 0, 1000, 1000)
        LOGGER.info("└── Test execution sequence completed.")
    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed: {ex}")
        sys.exit(1)