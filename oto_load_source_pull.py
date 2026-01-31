# sweep_loadpull_to_csv_one_row_per_state__all_tuple_inputs.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from itertools import product
from typing import Tuple, List, Union, Dict
import csv
import os
import time

from awr_loadpull_automation import AwrLoadPullAutomator, LoadPullParams
from awr_marker_reader import read_m1_values
from awr_hbtuner import set_tuner_mag_ang
from awr_udp_span_waiter import open_udp_listener, wait_begin_done_on_socket
from awr_schematic_setter import set_element_parameters


# ============================================================
# Helpers
# ============================================================
def fmt2(x) -> str:
    return f"{float(x):.2f}"  # nokta garantili

def frange(start: float, stop: float, step: float, *, include_stop: bool = True) -> List[float]:
    if step == 0:
        raise ValueError("step 0 olamaz")
    vals: List[float] = []
    x = start
    eps = 1e-9

    if step > 0:
        limit = stop + (eps if include_stop else -eps)
        while x <= limit:
            vals.append(round(x, 10))
            x += step
    else:
        limit = stop - (eps if include_stop else -eps)
        while x >= limit:
            vals.append(round(x, 10))
            x += step
    return vals

def make_tuple_from_sweep(start: float, stop: float, step: float, *, include_stop: bool = True) -> Tuple[float, ...]:
    return tuple(frange(start, stop, step, include_stop=include_stop))

ScalarOrTuple = Union[float, int, Tuple[float, ...], Tuple[int, ...]]

def normalize_to_tuple(x: ScalarOrTuple) -> Tuple[float, ...]:
    """
    Kullanıcı tek değer de verebilir, tuple da.
      normalize_to_tuple(-2.81) -> (-2.81,)
      normalize_to_tuple((12.75, 13.25)) -> (12.75, 13.25)
      normalize_to_tuple(29) -> (29.0,)
    """
    if isinstance(x, tuple):
        if len(x) == 0:
            raise ValueError("Boş tuple gönderilemez")
        return tuple(float(v) for v in x)
    # int/float tek değer
    return (float(x),)


# ============================================================
# Sweep Spec (ALL can be scalar OR tuple; internally normalized)
# ============================================================
@dataclass(frozen=True)
class SweepSpec:
    pin_in: ScalarOrTuple
    fo_in: ScalarOrTuple
    vgs_in: ScalarOrTuple

    @property
    def pin_list(self) -> Tuple[float, ...]:
        return normalize_to_tuple(self.pin_in)

    @property
    def fo_list(self) -> Tuple[float, ...]:
        return normalize_to_tuple(self.fo_in)

    @property
    def vgs_list(self) -> Tuple[float, ...]:
        return normalize_to_tuple(self.vgs_in)


# ============================================================
# State / Run specs
# ============================================================
@dataclass(frozen=True)
class State:
    pin_dbm: float
    fo_ghz: float
    vgs_v: float

@dataclass(frozen=True)
class RunSpec:
    n_iter: int = 3
    radius_list: Tuple[str, ...] = ("0.99", "0.40", "0.30")
    schematic_name: str = "VDS40_Load_Pull"
    host: str = "127.0.0.1"
    port: int = 50505
    udp_timeout_s: int = 100
    down_blast: int = 60

    element_port1_p1: str = "PORT1.P1"
    element_vgs: str = "DCVS.VGS"
    element_src_tuner: str = "HBTUNER3.SourceTuner"
    element_load_tuner: str = "HBTUNER3.LoadTuner"


# ============================================================
# Per-iteration row (internal)
# ============================================================
@dataclass
class ResultRow:
    pin_dbm: float
    fo_ghz: float
    vgs_v: float

    iter_no: int
    mode: str
    radius: str

    pload_dbm: str
    mag: str
    ang_deg: str

    timestamp_s: float


# ============================================================
# One-row-per-state summary (CSV output)
# ============================================================
@dataclass
class StateSummaryRow:
    pin_dbm: float
    fo_ghz: float
    vgs_v: float

    r1: str
    r2: str
    r3: str

    sp1_pload_dbm: str; sp1_mag: str; sp1_ang_deg: str
    sp2_pload_dbm: str; sp2_mag: str; sp2_ang_deg: str
    sp3_pload_dbm: str; sp3_mag: str; sp3_ang_deg: str

    lp1_pload_dbm: str; lp1_mag: str; lp1_ang_deg: str
    lp2_pload_dbm: str; lp2_mag: str; lp2_ang_deg: str
    lp3_pload_dbm: str; lp3_mag: str; lp3_ang_deg: str

    timestamp_s: float


def summarize_state_rows(state: State, rows: List[ResultRow], run_spec: RunSpec) -> StateSummaryRow:
    lookup: Dict[tuple, ResultRow] = {(r.mode, r.iter_no): r for r in rows}

    def get(mode: str, it: int) -> tuple[str, str, str]:
        rr = lookup.get((mode, it))
        if rr is None:
            return ("", "", "")
        return (rr.pload_dbm, rr.mag, rr.ang_deg)

    def radius_at(i0: int) -> str:
        if not run_spec.radius_list:
            return ""
        i0 = max(0, min(i0, len(run_spec.radius_list) - 1))
        return str(run_spec.radius_list[i0])

    r1 = radius_at(0)
    r2 = radius_at(1) if len(run_spec.radius_list) > 1 else r1
    r3 = radius_at(2) if len(run_spec.radius_list) > 2 else r2

    sp1 = get("SP", 1); sp2 = get("SP", 2); sp3 = get("SP", 3)
    lp1 = get("LP", 1); lp2 = get("LP", 2); lp3 = get("LP", 3)

    return StateSummaryRow(
        pin_dbm=state.pin_dbm, fo_ghz=state.fo_ghz, vgs_v=state.vgs_v,
        r1=r1, r2=r2, r3=r3,

        sp1_pload_dbm=sp1[0], sp1_mag=sp1[1], sp1_ang_deg=sp1[2],
        sp2_pload_dbm=sp2[0], sp2_mag=sp2[1], sp2_ang_deg=sp2[2],
        sp3_pload_dbm=sp3[0], sp3_mag=sp3[1], sp3_ang_deg=sp3[2],

        lp1_pload_dbm=lp1[0], lp1_mag=lp1[1], lp1_ang_deg=lp1[2],
        lp2_pload_dbm=lp2[0], lp2_mag=lp2[1], lp2_ang_deg=lp2[2],
        lp3_pload_dbm=lp3[0], lp3_mag=lp3[1], lp3_ang_deg=lp3[2],

        timestamp_s=time.time(),
    )


# ============================================================
# Runner
# ============================================================
class LoadPullSweepRunner:
    def __init__(self, run_spec: RunSpec):
        self.rs = run_spec
        self.bot = AwrLoadPullAutomator(down_blast=self.rs.down_blast)

    def radius_for(self, i: int) -> str:
        idx = max(0, i - 1)
        if idx >= len(self.rs.radius_list):
            idx = len(self.rs.radius_list) - 1
        return str(self.rs.radius_list[idx])

    def apply_state(self, st: State) -> None:
        out = set_element_parameters(
            schematic_name=self.rs.schematic_name,
            element_name_exact=self.rs.element_port1_p1,
            params={"Pwr": fmt2(st.pin_dbm), "Ang": "0"},
        )
        print(out)

        out = set_element_parameters(
            schematic_name=self.rs.schematic_name,
            element_name_exact=self.rs.element_vgs,
            params={"V": fmt2(st.vgs_v)},
        )
        print(out)

        out = set_element_parameters(
            schematic_name=self.rs.schematic_name,
            element_name_exact=self.rs.element_src_tuner,
            params={
                "Fo": fmt2(st.fo_ghz)
            },
        )
        print(out)

        out = set_element_parameters(
            schematic_name=self.rs.schematic_name,
            element_name_exact=self.rs.element_load_tuner,
            params={"Fo": fmt2(st.fo_ghz)},
        )
        print(out)

        set_tuner_mag_ang(self.rs.schematic_name, "SP", "calcMag(50,0,z0)", "calcAng(50,0,z0)")
        set_tuner_mag_ang(self.rs.schematic_name, "LP", "0", "0")

    def _run_one_mode(self, iter_no: int, mode: str, center_mag: str, angle_deg: str, radius: str) -> None:
        sock = open_udp_listener(host=self.rs.host, port=self.rs.port)
        try:
            self.bot.apply(
                iter_no=iter_no,
                mode=mode,
                params=LoadPullParams(angle_deg=angle_deg, center_mag=center_mag, radius=radius),
            )
            ok, span = wait_begin_done_on_socket(sock, timeout_s=self.rs.udp_timeout_s)
            if not ok:
                raise TimeoutError(f"[{mode}] BEGIN/DONE UDP gelmedi: {span}")
        finally:
            sock.close()

    def run_3iter_for_state(self, st: State) -> List[ResultRow]:
        results: List[ResultRow] = []
        prev_sp_mag, prev_sp_ang = 0.0, 0.0
        prev_lp_mag, prev_lp_ang = 0.0, 0.0

        for i in range(1, self.rs.n_iter + 1):
            r = self.radius_for(i)

            # SP
            self._run_one_mode(
                iter_no=i, mode="SP",
                center_mag=fmt2(prev_sp_mag) if i > 1 else "0",
                angle_deg=fmt2(prev_sp_ang) if i > 1 else "0",
                radius=r
            )
            sp_pload_dbm, sp_mag, sp_ang = read_m1_values(iter_no=i, mode="SP")
            print(f"STATE pin={st.pin_dbm} Fo={st.fo_ghz} Vgs={st.vgs_v} | SP iter{i} (r={r}):",
                  sp_pload_dbm, sp_mag, sp_ang)

            results.append(ResultRow(
                pin_dbm=st.pin_dbm, fo_ghz=st.fo_ghz, vgs_v=st.vgs_v,
                iter_no=i, mode="SP", radius=r,
                pload_dbm=str(sp_pload_dbm), mag=str(sp_mag), ang_deg=str(sp_ang),
                timestamp_s=time.time(),
            ))

            set_tuner_mag_ang(self.rs.schematic_name, "SP", fmt2(sp_mag), fmt2(sp_ang))
            set_tuner_mag_ang(self.rs.schematic_name, "LP", "calcMag(50,0,z0)", "calcAng(50,0,z0)")
            prev_sp_mag, prev_sp_ang = float(sp_mag), float(sp_ang)

            # LP
            self._run_one_mode(
                iter_no=i, mode="LP",
                center_mag=fmt2(prev_lp_mag) if i > 1 else "0",
                angle_deg=fmt2(prev_lp_ang) if i > 1 else "0",
                radius=r
            )
            lp_pload_dbm, lp_mag, lp_ang = read_m1_values(iter_no=i, mode="LP")
            print(f"STATE pin={st.pin_dbm} Fo={st.fo_ghz} Vgs={st.vgs_v} | LP iter{i} (r={r}):",
                  lp_pload_dbm, lp_mag, lp_ang)

            results.append(ResultRow(
                pin_dbm=st.pin_dbm, fo_ghz=st.fo_ghz, vgs_v=st.vgs_v,
                iter_no=i, mode="LP", radius=r,
                pload_dbm=str(lp_pload_dbm), mag=str(lp_mag), ang_deg=str(lp_ang),
                timestamp_s=time.time(),
            ))

            set_tuner_mag_ang(self.rs.schematic_name, "LP", fmt2(lp_mag), fmt2(lp_ang))
            set_tuner_mag_ang(self.rs.schematic_name, "SP", "calcMag(50,0,z0)", "calcAng(50,0,z0)")
            prev_lp_mag, prev_lp_ang = float(lp_mag), float(lp_ang)

        return results


# ============================================================
# CSV writer
# ============================================================
class CsvWriterSummary:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self._file = None
        self._writer = None
        self._header_written = False

    def __enter__(self):
        os.makedirs(os.path.dirname(self.csv_path) or ".", exist_ok=True)
        self._file = open(self.csv_path, "w", newline="", encoding="utf-8")
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._file:
            self._file.close()

    def write_summary(self, row: StateSummaryRow) -> None:
        d = asdict(row)
        if self._writer is None:
            self._writer = csv.DictWriter(self._file, fieldnames=list(d.keys()))
        if not self._header_written:
            self._writer.writeheader()
            self._header_written = True
        self._writer.writerow(d)
        self._file.flush()


# ============================================================
# State generation
# ============================================================
def generate_states(spec: SweepSpec) -> List[State]:
    pins = spec.pin_list
    fos = spec.fo_list
    vgs_list = spec.vgs_list

    if len(pins) == 0:
        raise ValueError("pin_in boş olamaz")
    if len(fos) == 0:
        raise ValueError("fo_in boş olamaz")
    if len(vgs_list) == 0:
        raise ValueError("vgs_in boş olamaz")

    return [State(pin_dbm=p, fo_ghz=fo, vgs_v=v) for (p, fo, v) in product(pins, fos, vgs_list)]


# ============================================================
# Main
# ============================================================
def main():
    # --------------------------------------------------------
    # Kullanıcı ister tuple, ister tek değer gönderebilir:
    #   pin_in = (28, 29)   veya pin_in = 28
    #   fo_in  = (12.75, 13.25) veya fo_in = 13.0
    #   vgs_in = -2.81      veya vgs_in = (-2.81, -3.00)
    #
    # Sweep'ten tuple üretmek için:
    #   make_tuple_from_sweep(26, 30, 1)
    # --------------------------------------------------------
    sweep = SweepSpec(
        pin_in=30,
        fo_in=13,
        vgs_in=-2.81,             # tek değer OK -> (-2.81,)
    )

    # Örnek sweep:
    # sweep = SweepSpec(
    #     pin_in=make_tuple_from_sweep(26, 30, 1),
    #     fo_in=(12.75, 13.00, 13.25),
    #     vgs_in=make_tuple_from_sweep(-2.0, -4.0, -0.25),
    # )

    run_spec = RunSpec(
        n_iter=2,
        radius_list=("0.99", "0.40", "0.30"),
        schematic_name="VDS40_Load_Pull",
        host="127.0.0.1",
        port=50505,
        udp_timeout_s=100,
        down_blast=60,
    )

    out_csv = "results/loadpull_sweep_results_one_row_per_state.csv"

    states = generate_states(sweep)
    print(f"Total states: {len(states)}")

    runner = LoadPullSweepRunner(run_spec)

    with CsvWriterSummary(out_csv) as cw:
        for k, st in enumerate(states, start=1):
            print(f"\n=== STATE {k}/{len(states)} | Pin={st.pin_dbm} dBm | Fo={st.fo_ghz} GHz | Vgs={st.vgs_v} V ===")
            try:
                runner.apply_state(st)
                rows = runner.run_3iter_for_state(st)
                summary = summarize_state_rows(st, rows, run_spec)
                cw.write_summary(summary)
            except Exception as e:
                print(f"[ERROR] State failed: {st} | {e}")

    print(f"DONE. CSV: {out_csv}")


if __name__ == "__main__":
    main()
