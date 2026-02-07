

# AWR Automated Load Pull Simulation Framework

This project provides a robust, modular, and professional automation framework for **AWR Microwave Office**. It orchestrates complex Source-Pull and Load-Pull simulation sequences, iterates through dynamic state variables, and logs extensive data with a structured, professional logging system.

## 📂 Project Structure

```text
.
├── main.py                               # Entry point of the simulation framework
├── config.py                             # Configuration constants (State vars, Tuner settings)
├── logger.py                             # Custom logging configuration (Colors, Formatting)
├── objects.py                            # Data classes (PullResult, StateType, etc.)
├── lp_iteration_point_selector.py        # Logic for selecting the best point on Smith Chart
├── pyawr_configure_schematic_element.py  # API wrapper for element configuration
├── pyawr_configure_schematic_rf_frequency.py # API wrapper for frequency settings
├── pyawr_get_marker_value.py             # API wrapper for reading graph markers
├── pyawr_loadpull_wizard.py              # API wrapper for controlling the Load Pull Wizard
├── simulation.log                        # Automatically generated log file
└── simulation_results.csv                # Output data file

```

## 🛠️ Prerequisites

* **Python 3.x**
* **AWR Microwave Office** (Installed and licensed)
* **`pyawr` Library:** (Standard AWR Python API)
* **`win32com`:** For COM interface communication.

## ⚙️ Configuration (`config.py`)

Before running the simulation, ensure your `config.py` is set up correctly. This file defines the search space and simulation parameters.

**Key Parameters:**

* `SCHEMATIC_NAME`: The target schematic in AWR.
* `STATE_VAR`: List of variables to sweep (e.g., `Freq`, `Vgs`, `Pin`).
* `MEASUREMENT_CONFIG`: Definitions of graphs and markers to record.
* `TUNER_SETTINGS`: Naming conventions for Source and Load tuners.

## ▶️ Usage

1. Open your AWR Microwave Office project.
2. Open a terminal in the project directory.
3. Run the main script:

```bash
python main.py

```

## 📊 Output & Logging

### Console Output

The framework provides a high-level, hierarchical view of the simulation progress in the console:

```text
INFO | >>> PROCESSING STATE 1/4: ('13.1', '30', '-2.75')
INFO |    > Iteration 1/3 (Radius: 0.99)
INFO |      * SP Result: Mag [0.843], Ang [-72.4]
INFO |      * LP Result: Mag [0.713], Ang [-121.5]
INFO |    > Iteration 2/3 (Radius: 0.50)
...
INFO | <<< STATE 1 COMPLETE

```

### File Logging (`simulation_year-month-day_hour-minute-second.log`)

Detailed technical logs, including API calls, parameter changes (`[Old] -> [New]`), and debugging information are saved to `simulation_year-month-day_hour-minute-second.log` in a clean, uncolored format suitable for auditing.

### Data Results (`simulation_results.csv`)

All simulation data, including state variables, optimal impedances (Source/Load), and measurement results (Gain, PAE, Power), are appended to this CSV file automatically.

## 🧩 Modules Description

* **`main.py`**: The brain of the operation. It initializes the `SimulationManager`, generates the state matrix, and runs the optimization loops.
* **`logger.py`**: Defines the `ProfessionalFormatter` class. It handles the dual-mode logging (Colored Console vs. Plain File) and tree-structure visual formatting.
* **`pyawr_*.py`**: These are atomic wrapper scripts. Each script handles a specific task within AWR (e.g., setting a frequency, reading a marker) and includes its own structured logging.

