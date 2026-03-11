from typing import Union, List, Tuple, Set, Any

from .element import Element
from awr.awr_component import AWRComponent


class Schematic(AWRComponent):

    def __init__(self, awr):
        super().__init__(awr)

        self.element = Element(self)

    def set_frequency(self, schematic_name: str, frequencies: Union[float, List[float]]) -> None:
        """Configures the RF simulation frequencies for a specific AWR schematic."""
        self.logger.info(f"├── Configuring RF Frequencies: '{schematic_name}'")

        try:
            project = self.app.Project

            if project.Schematics.Exists(schematic_name):
                schematic = project.Schematics(schematic_name)
                self.logger.debug(f"│   ├── Connected to schematic: {schematic_name}")

                if schematic.UseProjectFrequencies:
                    schematic.UseProjectFrequencies = False
                    self.logger.info(f"│   ├── Project defaults disabled.")

                old_count = schematic.Frequencies.Count
                schematic.Frequencies.Clear()
                self.logger.debug(f"│   ├── Cleared {old_count} existing points.")

                freq_list = [frequencies] if isinstance(frequencies, (int, float)) else frequencies
                total_freqs = len(freq_list)

                for i, freq in enumerate(freq_list):
                    schematic.Frequencies.Add(freq * 1e9)
                    is_last = (i == total_freqs - 1)
                    tree_char = "└──" if is_last else "├──"
                    self.logger.info(f"│   {tree_char} Added Frequency: {freq} GHz")

            else:
                self.logger.error(f"│   └── Schematic NOT found: '{schematic_name}'")
                raise ValueError(f"Schematic '{schematic_name}' is missing.")

        except Exception as e:
            self.logger.critical(f"│   └── Critical error in frequency config: {e}")
            raise

    def _get_schematic_obstacles(self, schematic: Any, exclude_points: List[Tuple[float, float]]) -> Tuple[Set[Tuple[float, float]], List[Tuple[float, float, float, float]]]:
        """Scans the schematic to map all pins (points) and existing wires (line segments)."""
        pins = set()
        wires = []

        for elem in schematic.Elements:
            for node in elem.Nodes:
                pins.add((node.x, node.y))

        for point in exclude_points:
            pins.discard(point)

        for wire in schematic.Wires:
            wires.append((wire.x1, wire.y1, wire.x2, wire.y2))

        return pins, wires

    def _is_segment_collinear_overlap(self, sx1: float, sy1: float, sx2: float, sy2: float,
                                      wx1: float, wy1: float, wx2: float, wy2: float) -> bool:
        """Checks if two line segments overlap collinearly."""
        if sx1 == sx2 and wx1 == wx2 and sx1 == wx1:
            min_s, max_s = min(sy1, sy2), max(sy1, sy2)
            min_w, max_w = min(wy1, wy2), max(wy1, wy2)
            if max(min_s, min_w) < min(max_s, max_w):
                return True

        elif sy1 == sy2 and wy1 == wy2 and sy1 == wy1:
            min_s, max_s = min(sx1, sx2), max(sx1, sx2)
            min_w, max_w = min(wx1, wx2), max(wx1, wx2)
            if max(min_s, min_w) < min(max_s, max_w):
                return True

        return False

    def _is_path_clear(self, path: List[Tuple[float, float]], pins: Set[Tuple[float, float]], wires: List[Tuple[float, float, float, float]]) -> bool:
        """Checks if a path intersects unintended pins or completely overlaps existing wires."""
        for i in range(len(path) - 1):
            sx, sy = path[i]
            ex, ey = path[i+1]

            for (ox, oy) in pins:
                if sx == ex == ox:
                    if min(sy, ey) <= oy <= max(sy, ey):
                        return False
                elif sy == ey == oy:
                    if min(sx, ex) <= ox <= max(sx, ex):
                        return False

            for (wx1, wy1, wx2, wy2) in wires:
                if self._is_segment_collinear_overlap(sx, sy, ex, ey, wx1, wy1, wx2, wy2):
                    return False

        return True

    def _generate_routing_candidates(self, x1: float, y1: float, x2: float, y2: float) -> List[List[Tuple[float, float]]]:
        """Generates an extensive prioritized list of orthogonal routing paths."""
        paths = []

        if x1 == x2 or y1 == y2:
            paths.append([(x1, y1), (x2, y2)])
            for offset in [100, -100, 200, -200, 300, -300]:
                if x1 == x2:
                    paths.append([(x1, y1), (x1 + offset, y1), (x2 + offset, y2), (x2, y2)])
                else:
                    paths.append([(x1, y1), (x1, y1 + offset), (x2, y1 + offset), (x2, y2)])
            return paths

        paths.append([(x1, y1), (x2, y1), (x2, y2)])
        paths.append([(x1, y1), (x1, y2), (x2, y2)])

        for offset in [100, -100, 200, -200, 300, -300, 400, -400]:
            paths.append([(x1, y1), (x1 + offset, y1), (x1 + offset, y2), (x2, y2)])
            paths.append([(x1, y1), (x1, y1 + offset), (x2, y1 + offset), (x2, y2)])
            paths.append([(x1, y1), (x2 + offset, y1), (x2 + offset, y2), (x2, y2)])
            paths.append([(x1, y1), (x1, y2 + offset), (x2, y2 + offset), (x2, y2)])

        return paths

    def add_wire(self, schematic_name: str, x1: float, y1: float, x2: float, y2: float) -> bool:
        """
        Draws a smart wire between two distinct coordinate points in the target schematic.
        It actively scans for other pins and existing wires to avoid short-circuits and visual overlaps.
        """
        try:
            schematic = self.app.Project.Schematics(schematic_name)

            pins, wires = self._get_schematic_obstacles(schematic, exclude_points=[(x1, y1), (x2, y2)])
            candidate_paths = self._generate_routing_candidates(x1, y1, x2, y2)

            best_path = None
            for idx, path in enumerate(candidate_paths):
                if self._is_path_clear(path, pins, wires):
                    best_path = path
                    if idx > 1:
                        self.logger.debug(f"│   ├── Route adjusted to candidate {idx + 1} to avoid channel overlap.")
                    break

            if not best_path:
                self.logger.warning(f"│   ├── Congested area detected. Forcing standard overlap route to preserve connectivity.")
                best_path = candidate_paths[0]

            for i in range(len(best_path) - 1):
                px1, py1 = best_path[i]
                px2, py2 = best_path[i+1]
                if (px1 != px2) or (py1 != py2):
                    schematic.Wires.Add(px1, py1, px2, py2)

            self.logger.debug(f"│   ├── Drawn smart channel-aware wire with {len(best_path) - 1} segment(s).")
            return True

        except Exception as e:
            self.logger.error(f"│   ├── Failed to draw wire from ({x1}, {y1}) to ({x2}, {y2}). Details: {e}")
            return False