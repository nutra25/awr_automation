"""
sequence.py
Encapsulates the Load-Pull specific optimization sequence.
Handles source/load iterations, wizard execution, and global maximum point selection.
Operates using strictly typed configuration objects via dependency injection.
"""

from typing import Tuple, Dict, Any, List
from dataclasses import dataclass
from rfdesign.loadpull.models import PullResult
from logger.logger import LOGGER
from dataexporter.dataexporter import DataExporter
from rfdesign.loadpull.tuner_utils import PullType, build_tuner_params, TunerConfig


@dataclass
class WizardSettingsConfig:
    """Configuration node specifically for AWR Load-Pull Wizard parameters."""
    max_harmonic: int = 1
    overwrite_data_file: bool = True
    data_file_pattern: str = "{side}_pull_data_{iter}"
    density: str = "Extra fine"


@dataclass
class SequenceConfig:
    """Configuration node for the Load-Pull Sequence logic."""
    schematic_name: str
    tuner_settings: TunerConfig
    wizard_settings: WizardSettingsConfig
    measurement_config: List[Dict[str, Any]]
    graph_name_pattern: str
    point_selector: Any
    iteration_count: int
    radius_list: Tuple[float, ...]

    default_mag_expr: str = "calcMag(50,0,z0)"
    default_ang_expr: str = "calcAng(50,0,z0)"
    source_pull_prefix: str = "SP"
    load_pull_prefix: str = "LP"


class LoadPullSequence:
    """
    Executes the Load-Pull specific wizard operations and measurement extractions.
    """

    def __init__(self, driver: Any, exporter: DataExporter, config: SequenceConfig):
        self.driver = driver
        self.exporter = exporter
        self.config = config

    def _build_wizard_payload(self, active_side: str, fixed_side: str, iter_idx: int, radius: float, center_mag: float, center_ang: float) -> dict:
        """Dynamically generates the required AWR Wizard dictionary using structured config."""
        cfg = self.config.wizard_settings
        h = cfg.max_harmonic
        active_cap = active_side.capitalize()
        fixed_cap = fixed_side.capitalize()

        return {
            "LP_MaxHarmonic": h,
            "LP_DataFileName": cfg.data_file_pattern.format(side=active_side.lower(), iter=iter_idx),
            "LP_OverwriteDataFile": cfg.overwrite_data_file,
            f"LP_Sweep_{active_cap}{h}": True,
            f"LP_Sweep_{fixed_cap}{h}": False,
            f"LP_{active_cap}{h}_Density": cfg.density,
            f"LP_{active_cap}{h}_Radius": radius,
            f"LP_{active_cap}{h}_CenterMagnitude": center_mag,
            f"LP_{active_cap}{h}_CenterAngle": center_ang
        }

    def _run_iteration(self, iter_idx: int, pull_type: PullType,
                       radius: float, sweep_center: Tuple[float, float],
                       fixed_pos: Tuple[float, float], export_subpath: str) -> PullResult:

        is_source = (pull_type == PullType.SOURCEPULL)
        h_idx = self.config.wizard_settings.max_harmonic
        active_side = "SOURCE" if is_source else "LOAD"
        fixed_side = "LOAD" if is_source else "SOURCE"
        mode_prefix = self.config.source_pull_prefix if is_source else self.config.load_pull_prefix

        active_params = build_tuner_params(
            self.config.tuner_settings, active_side,
            self.config.default_mag_expr, self.config.default_ang_expr, h_idx
        )

        if isinstance(fixed_pos, (list, tuple)) and len(fixed_pos) >= 2:
            fixed_params = build_tuner_params(self.config.tuner_settings, fixed_side, fixed_pos[0], fixed_pos[1], h_idx)
            center_ang = sweep_center[1] if isinstance(sweep_center, (list, tuple)) and len(sweep_center) >= 2 else sweep_center
        else:
            fixed_params = build_tuner_params(self.config.tuner_settings, fixed_side, fixed_pos, fixed_pos, h_idx)
            center_ang = sweep_center

        self.driver.circuit.configure_element(
            self.config.schematic_name, self.config.tuner_settings.source.name,
            active_params if is_source else fixed_params
        )
        self.driver.circuit.configure_element(
            self.config.schematic_name, self.config.tuner_settings.load.name,
            fixed_params if is_source else active_params
        )

        center_mag = sweep_center[0] if isinstance(sweep_center, (list, tuple)) else sweep_center


        wizard_opts = self._build_wizard_payload(
            active_side=active_side,
            fixed_side=fixed_side,
            iter_idx=iter_idx,
            radius=radius,
            center_mag=center_mag,
            center_ang=center_ang
        )

        self.driver.wizard.run_wizard(wizard_opts)

        graph_name = self.config.graph_name_pattern.format(iter=iter_idx, type=active_side.lower())

        point, mag, ang = self.config.point_selector.select_point(
            self.driver,
            graph_name,
            exporter=self.exporter,
            export_subpath=export_subpath
        )

        return PullResult(
            iter_no=iter_idx,
            mode=mode_prefix,
            point=point,
            mag=float(mag),
            ang=float(ang)
        )

    def _finalize_state(self, results: List[PullResult]) -> Tuple[Dict, Tuple]:
        best_lp = max((x for x in results if x.mode == self.config.load_pull_prefix), key=lambda x: float(x.point))
        best_sp = next(res for res in results if res.iter_no == best_lp.iter_no and res.mode == self.config.source_pull_prefix)

        self.driver.circuit.configure_element(
            self.config.schematic_name, self.config.tuner_settings.source.name,
            build_tuner_params(self.config.tuner_settings, "SOURCE", best_sp.mag, best_sp.ang)
        )
        self.driver.circuit.configure_element(
            self.config.schematic_name, self.config.tuner_settings.load.name,
            build_tuner_params(self.config.tuner_settings, "LOAD", best_lp.mag, best_lp.ang)
        )

        measured_data = {}
        for m in self.config.measurement_config:
            self.driver.graph.toggle_measurements(m["graph"], enable=True)
            self.driver.graph.move_marker(graph_name=m["graph"], marker_name=m["marker"], action="MIN", perform_simulation=True)
            data = self.driver.graph.get_marker_data(m["graph"], m["marker"], toggle_enable=False)
            self.driver.graph.toggle_measurements(m["graph"], enable=False)
            idx = int(m["index"])
            val = str(data[idx]) if len(data) > idx else "NaN"
            measured_data[m["header"]] = val

        tuner_data = (str(best_sp.mag), str(best_sp.ang),
                      str(best_lp.mag), str(best_lp.ang))

        return measured_data, tuner_data

    def execute(self, export_subpath: str) -> Tuple[Dict, List[PullResult], Tuple]:
        current_results = []
        pos = {PullType.SOURCEPULL: (0.0, 0.0), PullType.LOADPULL: (0.0, 0.0)}

        for i in range(self.config.iteration_count):
            radius = float(self.config.radius_list[i])
            iter_num = i + 1

            LOGGER.info(f"│   ├── Iteration {iter_num}/{self.config.iteration_count} (Radius: {radius})")

            sp_res = self._run_iteration(
                iter_num, PullType.SOURCEPULL, radius,
                pos[PullType.SOURCEPULL], pos[PullType.LOADPULL],
                export_subpath
            )
            current_results.append(sp_res)
            pos[PullType.SOURCEPULL] = (float(sp_res.mag), float(sp_res.ang))
            LOGGER.info(f"│   ├── SP Result: Mag [{sp_res.mag:.3f}], Ang [{sp_res.ang:.1f}]")

            lp_res = self._run_iteration(
                iter_num, PullType.LOADPULL, radius,
                pos[PullType.LOADPULL], pos[PullType.SOURCEPULL],
                export_subpath
            )
            current_results.append(lp_res)
            pos[PullType.LOADPULL] = (float(lp_res.mag), float(lp_res.ang))
            LOGGER.info(f"│   └── LP Result: Mag [{lp_res.mag:.3f}], Ang [{lp_res.ang:.1f}]")

        LOGGER.debug("│   ├── Finalizing state configuration and preparing data export...")
        measured_data, tuner_data = self._finalize_state(current_results)

        return measured_data, current_results, tuner_data