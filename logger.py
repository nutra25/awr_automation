import logging
import sys
from datetime import datetime

# #################################################
# COLORS AND STYLES
class LogColors:
    """
    Defines ANSI escape sequences for terminal coloring and maps specific
    filenames to distinct colors for better visual separation in logs.
    """
    RESET = "\033[0m"
    GRAY  = "\033[0;37m"  # Silver/Gray for separators and timestamps

    # Bright colors for filenames (No background)
    B_RED     = "\033[0;91m"
    B_GREEN   = "\033[0;92m"
    B_YELLOW  = "\033[0;93m"
    B_BLUE    = "\033[0;94m"
    B_PURPLE  = "\033[0;95m"
    B_CYAN    = "\033[0;96m"
    B_WHITE   = "\033[0;97m"

    # Mapping of filenames to specific colors for quick visual identification
    FILE_COLORS = {
        "gemini.py": B_GREEN,
        "main.py": B_GREEN,
        "pyawr_loadpull_wizard.py": B_PURPLE,
        "pyawr_configure_schematic_element.py": B_BLUE,
        "pyawr_configure_schematic_rf_frequency.py": B_YELLOW,
        "pyawr_get_marker_value.py": B_CYAN,
    }
    DEFAULT_FILE_COLOR = B_WHITE
# #################################################

class ProfessionalFormatter(logging.Formatter):
    """
    Custom log formatter that handles ANSI coloring, multi-line message collapsing,
    and consistent column alignment for both console and file outputs.
    """
    LEVEL_COLORS = {
        logging.DEBUG: LogColors.GRAY,
        logging.INFO:  "\033[0;97m",
        logging.WARNING: LogColors.B_YELLOW,
        logging.ERROR:   LogColors.B_RED,
        logging.CRITICAL: "\033[1;31m",
    }

    def __init__(self, use_colors=True):
        """
        Args:
            use_colors (bool): If True, ANSI color codes are applied to the output.
                               Set to False for file logging to ensure clean text.
        """
        super().__init__()
        self.use_colors = use_colors

    def format(self, record):
        # Retrieve the original log message
        msg = record.getMessage()

        # Handle multi-line messages (e.g., from exceptions or complex data)
        # The goal is to collapse them into a single line while preserving the
        # visual tree structure indentation of the first line.
        if "\n" in msg:
            lines = [line for line in msg.splitlines() if line.strip()]

            if lines:
                # IMPORTANT: Use rstrip() only. This removes trailing whitespace/newlines
                # but preserves the leading whitespace (indentation) required for the tree view.
                first_line = lines[0].rstrip()

                # For subsequent lines, strip all whitespace and join them with a separator
                other_lines = [line.strip() for line in lines[1:]]

                if other_lines:
                    msg = f"{first_line} ({' | '.join(other_lines)})"
                else:
                    msg = first_line

        # Escape percentage signs to prevent formatting errors in the logging system
        msg = msg.replace("%", "%%")

        # Format the timestamp
        time_str = self.formatTime(record, '%H:%M:%S')

        # ---------------------------------------------------------
        # COLORED FORMAT (FOR CONSOLE)
        # ---------------------------------------------------------
        if self.use_colors:
            lvl_color = self.LEVEL_COLORS.get(record.levelno, LogColors.B_WHITE)
            file_color = LogColors.FILE_COLORS.get(record.filename, LogColors.DEFAULT_FILE_COLOR)
            line_color = LogColors.GRAY
            reset = LogColors.RESET

            f_time = f"{line_color}{time_str}{reset}"
            f_sep  = f"{line_color}|{reset}"
            f_file = f"{file_color}{record.filename:<42}{reset}"
            f_lvl  = f"{lvl_color}{record.levelname:<8}{reset}"
            f_msg  = f"{lvl_color}{msg}{reset}"

            return f"{f_time} {f_sep} {f_file} {f_sep} {f_lvl} {f_sep} {f_msg}"

        # ---------------------------------------------------------
        # PLAIN FORMAT (FOR FILE)
        # ---------------------------------------------------------
        else:
            # Returns clean text without ANSI codes but maintains the same padding/alignment
            return f"{time_str} | {record.filename:<42} | {record.levelname:<8} | {msg}"

# LOGGER CONFIGURATION
LOGGER = logging.getLogger("awr_automation")
LOGGER.setLevel(logging.DEBUG)

if LOGGER.hasHandlers():
    LOGGER.handlers.clear()

# -----------------------------------------------------------------------------
# 1. SETUP LOG FILENAME WITH TIMESTAMP
# -----------------------------------------------------------------------------
now = datetime.now()
# Format: simulation_YYYY-MM-DD_HH-MM-SS.log
log_filename = f"simulation_{now.strftime('%Y-%m-%d_%H-%M-%S')}.log"

# Write a clean header to the new file before attaching the logger
with open(log_filename, "w", encoding="utf-8") as f:
    header_date = now.strftime("%d.%m.%Y %H:%M")
    f.write(f"LOG SESSION DATE: {header_date}\n")
    f.write("-" * 50 + "\n")

# -----------------------------------------------------------------------------
# 2. CONSOLE HANDLER (Live Monitoring)
# -----------------------------------------------------------------------------
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(ProfessionalFormatter(use_colors=True))

# -----------------------------------------------------------------------------
# 3. FILE HANDLER (Persistent Storage)
# -----------------------------------------------------------------------------
# Use mode='a' (append) to preserve the header we just wrote
file_handler = logging.FileHandler(log_filename, mode='a', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(ProfessionalFormatter(use_colors=False))

LOGGER.addHandler(console_handler)
LOGGER.addHandler(file_handler)

__all__ = ['LOGGER', 'LogColors']