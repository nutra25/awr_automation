"""
sequence.py
Encapsulates the Load-Pull specific optimization sequence.
Handles source/load iterations, wizard execution, and global maximum point selection.
Operates using strictly typed configuration objects via dependency injection.
"""

from typing import Tuple, Dict, Any, List
import objects
from logger.logger import LOGGER
from dataexporter.dataexporter import DataExporter
from config import SequenceConfig

# Import isolated utilities instead of defining them internally
from rfdesign.loadpull.tuner_utils import PullType, build_tuner_params


class LoadPullSequence:
    """
    Executes the Load-Pull specific wizard operations and measurement extractions.
    Completely decoupled from global project configurations, utilizing SequenceConfig.
    """

    def __init__(self, driver: Any, exporter: DataExporter, config: SequenceConfig):
        """
        Initializes the sequence with the strictly typed configuration branch.
        """
        self.driver = driver
        self.exporter = exporter
        self.config = config

    def _run_iteration(self, iter_idx: int, pull_type: PullType,
                       radius: float, sweep_center: Tuple[float, float],
                       fixed_pos: Tuple[float, float], export_subpath: str) -> objects.PullResult:
        """
        Executes a single Source or Load pull iteration step.
        Configures the tuners, runs the wizard, and delegates graphic export.
        """
        is_source = (pull_type == PullType.SOURCEPULL)
        h_idx = 1
        active_side = "SOURCE" if is_source else "LOAD"
        fixed_side = "LOAD" if is_source else "SOURCE"

        # Use the injected tuner settings from the configuration object
        active_params = build_tuner_params(
            self.config.tuner_settings, active_side, "calcMag(50,0,z0)", "calcAng(50,0,z0)", h_idx
        )

        if isinstance(fixed_pos, (list, tuple)) and len(fixed_pos) >= 2:
            fixed_params = build_tuner_params(self.config.tuner_settings, fixed_side, fixed_pos[0], fixed_pos[1], h_idx)
            center_ang = sweep_center[1] if isinstance(sweep_center, (list, tuple)) and len(sweep_center) >= 2 else sweep_center
        else:
            fixed_params = build_tuner_params(self.config.tuner_settings, fixed_side, fixed_pos, fixed_pos, h_idx)
            center_ang = sweep_center

        # FIXED: Accessed dataclass properties using dot notation instead of dictionary keys
        self.driver.circuit.configure_element(
            self.config.schematic_name, self.config.tuner_settings.source.name,
            active_params if is_source else fixed_params
        )
        self.driver.circuit.configure_element(
            self.config.schematic_name, self.config.tuner_settings.load.name,
            fixed_params if is_source else active_params
        )

        wizard_opts = {
            "LP_MaxHarmonic": h_idx,
            "LP_DataFileName": f"{active_side.lower()}_pull_data_{iter_idx}",
            "LP_OverwriteDataFile": True,
            f"LP_Sweep_{active_side.capitalize()}{h_idx}": True,
            f"LP_Sweep_{fixed_side.capitalize()}{h_idx}": False,
            f"LP_{active_side.capitalize()}{h_idx}_Density": "Extra fine",
            f"LP_{active_side.capitalize()}{h_idx}_Radius": radius,
            f"LP_{active_side.capitalize()}{h_idx}_CenterMagnitude": sweep_center[0] if isinstance(sweep_center, (list, tuple)) else sweep_center,
            f"LP_{active_side.capitalize()}{h_idx}_CenterAngle": center_ang
        }

        self.driver.wizard.run_wizard(wizard_opts)

        graph_name = self.config.graph_name_pattern.format(iter=iter_idx, type=active_side.lower())

        point, mag, ang = self.config.point_selector.select_point(
            self.driver,
            graph_name,
            exporter=self.exporter,
            export_subpath=export_subpath
        )

        return objects.PullResult(
            iter_no=iter_idx,
            mode="SP" if is_source else "LP",
            point=point,
            mag=float(mag),
            ang=float(ang)
        )

    def _finalize_state(self, results: List[objects.PullResult]) -> Tuple[Dict, Tuple]:
        """
        Identifies the global maximum results, sets the tuners, and captures final measurements.
        """
        best_lp = max((x for x in results if x.mode == "LP"), key=lambda x: float(x.point))
        best_sp = next(res for res in results if res.iter_no == best_lp.iter_no and res.mode == "SP")

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
            data = self.driver.graph.get_marker_data(m["graph"], m["marker"], toggle_enable=True)
            val = str(data[m["index"]]) if len(data) > m["index"] else "NaN"
            measured_data[m["header"]] = val

        tuner_data = (str(best_sp.mag), str(best_sp.ang),
                      str(best_lp.mag), str(best_lp.ang))

        return measured_data, tuner_data

    def execute(self, export_subpath: str) -> Tuple[Dict, List[objects.PullResult], Tuple]:
        """
        Main execution loop for a single state.
        Runs predefined iterations and returns the final measurements and results.
        """
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


if __name__ == "__main__":
    import sys
    LOGGER.info("├── Starting standalone test sequence for sequence.py")
    try:
        from rfdesign.loadpull.tuner_utils import TunerConfig, TunerSideConfig

        class DummySelector:
            def select_point(self, driver, graph, exporter, export_subpath):
                return "10.0", "0.5", "45.0"

        dummy_tuner_config = TunerConfig(
            source=TunerSideConfig(name="S", prefix_mag="M", prefix_ang="A"),
            load=TunerSideConfig(name="L", prefix_mag="M", prefix_ang="A")
        )

        dummy_config = SequenceConfig(
            schematic_name="Test_Schematic",
            tuner_settings=dummy_tuner_config,
            measurement_config=[],
            graph_name_pattern="test_{iter}_{type}",
            point_selector=DummySelector(),
            iteration_count=1,
            radius_list=("0.99",)
        )

        seq = LoadPullSequence(driver=None, exporter=None, config=dummy_config)
        LOGGER.info(f"│   ├── Sequence Config Schematic: {seq.config.schematic_name}")
        LOGGER.info(f"│   ├── Tuner Source Name: {seq.config.tuner_settings.source.name}")
        LOGGER.info("└── Test execution sequence completed successfully")
    except Exception as ex:
        LOGGER.critical(f"└── Test execution failed: {ex}")
        sys.exit(1)