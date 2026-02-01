import config
import logging
import itertools
from typing import List, Tuple
import objects
import csv
from enum import Enum, auto
from awr_loadpull_automation import AwrLoadPullAutomator, LoadPullParams
from awr_marker_reader import read_marker_raw_text
from awr_schematic_setter import set_element_parameters
import re
# ============================================================
# LOGGING CONFIGURATION
# Configures output to both console and a persistent log file.
# Format: Date Time | Log Level | Message
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-1s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        # File Handler: Overwrites the log file on each new run (mode='w').
        logging.FileHandler("simulation.log", mode='w', encoding='utf-8'),

        # Stream Handler: Outputs logs to the console standard output.
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("awr_automation")

class PullType(Enum):
    """Enumeration defining the operation mode: Load Pull or Source Pull."""
    LOADPULL = auto()
    SOURCEPULL = auto()

class SimulationRunner:
    """
    Orchestrates the automated Load Pull and Source Pull simulation process.

    Responsibilities:
    1. Generates all permutations of state variables (Frequency, Voltage, etc.).
    2. Executes iterative Pull simulations for each state.
    3. Manages data acquisition and logging to CSV.
    """

    def __init__(self):
        """Initializes the simulation runner and prepares the output CSV file."""
        self.csv_filename = "simulation_results.csv"
        self.csv_file = None
        self.csv_writer = None

        # Initialize the CSV file with dynamic headers
        self._initialize_csv()

    def _initialize_csv(self):
        """
        Creates the CSV file and writes the header row.

        The header includes:
        1. State Variable Names (from config).
        2. Measurement Columns (dynamically generated based on iteration count).
        """
        # 1. Retrieve State Variable Headers
        state_headers = [var.name for var in config.STATE_VAR]

        # 2. Generate Measurement Headers
        measure_headers = []
        for i in range(config.ITERATION_COUNT):
            iter_num = i + 1
            # Generate headers for Source Pull (SP) results
            measure_headers.extend([
                f"SP_Iter{iter_num}_Point",
                f"SP_Iter{iter_num}_Mag",
                f"SP_Iter{iter_num}_Ang"
            ])
            # Generate headers for Load Pull (LP) results
            measure_headers.extend([
                f"LP_Iter{iter_num}_Point",
                f"LP_Iter{iter_num}_Mag",
                f"LP_Iter{iter_num}_Ang"
            ])

        # 3. Open File and Write Headers
        full_headers = state_headers + measure_headers
        try:
            self.csv_file = open(self.csv_filename, mode='w', newline='', encoding='utf-8')
            self.csv_writer = csv.writer(self.csv_file)
            self.csv_writer.writerow(full_headers)

            # Flush immediately to ensure headers are persisted
            self.csv_file.flush()
            logger.info(f"CSV Initialized: {self.csv_filename}")
        except IOError as e:
            logger.error(f"Failed to initialize CSV file: {e}")
            raise

    def _write_state_to_csv(self, state_values: Tuple[str, ...], iteration_results: List[objects.PullResult]):
        """
        Flattens the simulation results for a single state and appends a row to the CSV.

        Args:
            state_values: Tuple containing values for the current state (e.g., Freq, Vgs).
            iteration_results: List of result objects from the iterative pull process.
        """
        row_data = []

        # Append State Values (e.g., "13.0", "30")
        row_data.extend(state_values)

        # Append Measurement Results
        # Iterates through stored results and extracts Point, Magnitude, and Angle.
        for res in iteration_results:
            row_data.extend([res.point, res.mag, res.ang])

        # Write to file and flush buffer to protect against data loss during crashes
        if self.csv_writer:
            self.csv_writer.writerow(row_data)
            self.csv_file.flush()
            logger.info(f"Data saved to CSV -> State: {state_values}")

    @staticmethod
    def _set_schematic_element_value(element_name_exact: str, params: dict):
        logger.info(f"  ->[API][awr_schematic_setter] SENT:[schematic_name:({config.SCHEMATIC_NAME}) element_name_exact:({element_name_exact}) params:({params})]")
        out = set_element_parameters(
            schematic_name=config.SCHEMATIC_NAME,
            element_name_exact=element_name_exact,
            params=params,
        )

    @staticmethod
    def _get_graph_data(iteration: int, pull_type: PullType, marker: str) -> objects.PullResult:
        """
        Simulates the retrieval of marker data from the AWR environment.
        Args:
            iteration: Current iteration index.
            pull_type: Operation mode (Source Pull or Load Pull).
        Returns:
            A PullResult object containing the simulated measured data.
        """
        pull_type_str = "SP" if pull_type == PullType.SOURCEPULL else "LP"
        graph_name = f"it{iteration}" + "_source_pull" if pull_type == PullType.SOURCEPULL else f"it{iteration}" + "_load_pull"

        out = read_marker_raw_text(
            graph_name=graph_name,
            marker_name=marker,
            simulate=True
        )
        numbers = re.findall(r"-?\d+\.?\d*", out)

        numbers = [float(n) for n in numbers]

        point = numbers[0]
        mag = numbers[1]
        ang = numbers[2]

        logger.info(f"  ->[API][awr_marker_reader] SENT:[graph_name:({graph_name}) marker:({marker})] -> RECEIVED:[point:({point}) mag:({mag}) ang:({ang})]")

        return objects.PullResult(
            iter_no=iteration,
            mode=pull_type_str,
            point=str(point),
            mag=str(mag),
            ang=str(ang)
        )

    @staticmethod
    def _run_pull_sim( iteration: int, pull_type: PullType, radius: str, centermag: str, centerang: str):
        """
        Simulates the simulation of Load/Source Pull analysis from the AWR environment.
        Args:
            iteration: Current iteration index.
            pull_type: Operation mode (Source Pull or Load Pull).
        """
        pull_type_str = "SP" if pull_type == PullType.SOURCEPULL else "LP"
        logger.info(f"  ->[API][awr_loadpull_automation] SENT:[iteration:({iteration}) pull_type:({pull_type_str}) radius:({radius}) center_mag:({centermag}) center_ang:({centerang})]")
        bot = AwrLoadPullAutomator(down_blast=config.DOWN_BLAST)
        bot.apply(
            iter_no=iteration,
            mode=pull_type_str,
            params=LoadPullParams(angle_deg=centerang, center_mag=centermag, radius=radius),
        )
    def _run_single_state_logic(self, state_values: Tuple[str, ...]):
        """
        Executes the iterative simulation logic for a specific combination of state variables.

        Logic Flow:
        1. Sets the environment state (Frequency, Bias, etc.).
        2. Performs alternating Source Pull and Load Pull simulations.
        3. Implements 'Center Shifting': The result of the previous pull becomes the
           center for the next pull operation.
        4. Logs all aggregated results to CSV upon completion.

        Args:
            state_values: Tuple of values defining the current simulation state.
        """

        # 1. Set State Variables in the Environment
        # ------------------------------------------------
        for idx, val in enumerate(state_values):
            var_obj = config.STATE_VAR[idx]
            logger.info(f"SET STATE: {var_obj.name} = {val}")
            for _, elem in enumerate(var_obj.element):
                self._set_schematic_element_value(
                    element_name_exact=elem.name,
                    params = {elem.arg: val}
                )

                # Actual AWR element update logic would be invoked here.

        # 2. Initialize Center Shifting Parameters
        # ------------------------------------------------
        # Start the first iteration from the center of the Smith Chart (or defined origin).
        prev_sp_mag, prev_sp_ang = "0", "0"
        prev_lp_mag, prev_lp_ang = "0", "0"

        # Local storage for results of this specific state
        current_state_results: List[objects.PullResult] = []

        # 3. Execute Iterative Pull Operations
        # ------------------------------------------------
        for i in range(config.ITERATION_COUNT):
            current_radius = config.RADIUS_LIST[i]
            logger.info(f"--- Iteration {i + 1} (Radius: {current_radius}) ---")

            # === SOURCE PULL (SP) ===
            self._set_schematic_element_value(
                element_name_exact="HBTUNER3.SourceTuner",
                params={"Mag1": "calcMag(50,0,z0)", "Ang1": "calcAng(50,0,z0)"}
            )
            self._set_schematic_element_value(
                element_name_exact="HBTUNER3.LoadTuner",
                params={"Mag1": prev_lp_mag, "Ang1": prev_lp_ang}
            )
            self._run_pull_sim(
                iteration=i+1,
                pull_type=PullType.SOURCEPULL,
                radius=current_radius,
                centermag=prev_sp_mag,
                centerang=prev_sp_ang
            )
            sp_res = self._get_graph_data(
                iteration=i+1,
                pull_type=PullType.SOURCEPULL,
                marker=config.MARKER
            )
            current_state_results.append(sp_res)

            # Update Center: The optimal point found in SP becomes the center for the next SP step.
            prev_sp_mag = sp_res.mag
            prev_sp_ang = sp_res.ang

            # === LOAD PULL (LP) ===
            self._set_schematic_element_value(
                element_name_exact="HBTUNER3.SourceTuner",
                params={"Mag1": prev_sp_mag, "Ang1": prev_sp_ang}
            )
            self._set_schematic_element_value(
                element_name_exact="HBTUNER3.LoadTuner",
                params={"Mag1": "calcMag(50,0,z0)", "Ang1": "calcAng(50,0,z0)"}
            )
            self._run_pull_sim(
                iteration=i+1,
                pull_type=PullType.LOADPULL,
                radius=current_radius,
                centermag=prev_lp_mag,
                centerang=prev_lp_ang
            )
            lp_res = self._get_graph_data(
                iteration=i+1,
                pull_type=PullType.LOADPULL,
                marker=config.MARKER
            )
            current_state_results.append(lp_res)
            # Update Center: The optimal point found in LP becomes the center for the next LP step.
            prev_lp_mag = lp_res.mag
            prev_lp_ang = lp_res.ang

        # 4. Finalize: Write Aggregated Results to CSV
        # ------------------------------------------------
        self._write_state_to_csv(state_values, current_state_results)

        logger.info("--- State Completed ---\n")

    def start(self):
        """
        Main execution loop.

        1. Calculates the Cartesian product of all state variables to determine
           every unique combination (permutation) to be simulated.
        2. Iterates through these combinations and executes the simulation logic.
        3. Ensures the CSV file is closed properly upon completion or failure.
        """
        try:
            for _, cons_obj in enumerate(config.STATE_CONS):
                logger.info(f"SET CONSTANT: {cons_obj.name} = {cons_obj.value[0]}")
                for _, elem in enumerate(cons_obj.element):
                    self._set_schematic_element_value(
                        element_name_exact=elem.name,
                        params={elem.arg: cons_obj.value[0]}
                    )

            # Generate all possible state combinations using Cartesian product
            all_values_lists = [v.value for v in config.STATE_VAR]
            all_combinations = list(itertools.product(*all_values_lists))

            logger.info(f"Total States to Simulate: {len(all_combinations)}")

            # Execute simulation for each combination
            for combo in all_combinations:
                self._run_single_state_logic(state_values=combo)

            logger.info("Simulation Completed Successfully.")

        finally:
            # Ensure resources are released
            if self.csv_file:
                self.csv_file.close()
                logger.info("CSV File Closed.")


def main():
    """Entry point for the automation script."""
    sim = SimulationRunner()
    sim.start()



if __name__ == "__main__":
    main()