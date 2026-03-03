"""
logger.py
Provides a highly modular, dynamic color-assigning logger that enforces
a tree-branch structure for all logging activities across the project.
Operates via a dedicated configuration object for strict dependency management.
"""

import logging
import sys
import os
import hashlib
from datetime import datetime
from dataclasses import dataclass

# Import the default path configuration for global fallback initialization
from paths import default_paths


@dataclass
class LoggerConfig:
    """
    Configuration node for the logging infrastructure.
    """
    log_dir: str
    log_name: str = "simulation.log"
    use_colors: bool = True


class LogColors:
    """
    Defines ANSI escape sequences for terminal coloring.
    """
    RESET = "\033[0m"
    GRAY = "\033[0;37m"
    B_RED = "\033[0;91m"
    B_YELLOW = "\033[0;93m"
    B_WHITE = "\033[0;97m"

    DYNAMIC_PALETTE = [
        "\033[0;92m",  # B_GREEN
        "\033[0;94m",  # B_BLUE
        "\033[0;95m",  # B_PURPLE
        "\033[0;96m",  # B_CYAN
        "\033[38;2;130;145;55m",  # KHAKI_MILITARY
        "\033[38;2;180;30;60m",   # CHERRY
        "\033[38;2;255;165;0m",   # ORANGE
        "\033[38;2;0;250;154m"    # MEDIUM_SPRING_GREEN
    ]


class ProfessionalFormatter(logging.Formatter):
    """
    Custom log formatter handling ANSI coloring and dynamic file color mapping.
    Ensures serious, professional output formatting with strict column alignment.
    """
    LEVEL_COLORS = {
        logging.DEBUG: LogColors.GRAY,
        logging.INFO: LogColors.B_WHITE,
        logging.WARNING: LogColors.B_YELLOW,
        logging.ERROR: LogColors.B_RED,
        logging.CRITICAL: "\033[1;31m",
    }

    FILE_COLUMN_WIDTH = 45

    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors
        self._color_cache = {}

    def _get_dynamic_file_color(self, filename: str) -> str:
        """
        Assigns a consistent color from the palette based on the hash of the filename.
        """
        if filename not in self._color_cache:
            hash_val = int(hashlib.md5(filename.encode('utf-8')).hexdigest(), 16)
            color_index = hash_val % len(LogColors.DYNAMIC_PALETTE)
            self._color_cache[filename] = LogColors.DYNAMIC_PALETTE[color_index]
        return self._color_cache[filename]

    def format(self, record: logging.LogRecord) -> str:
        msg = record.getMessage().rstrip()

        # Handle multi-line messages while preserving the tree-branch structure
        if "\n" in msg:
            lines = [line for line in msg.splitlines() if line.strip()]
            if lines:
                first_line = lines[0].rstrip()
                other_lines = [line.strip() for line in lines[1:]]
                msg = f"{first_line} ({' | '.join(other_lines)})" if other_lines else first_line

        msg = msg.replace("%", "%%")
        time_str = self.formatTime(record, '%H:%M:%S')

        if self.use_colors:
            lvl_color = self.LEVEL_COLORS.get(record.levelno, LogColors.B_WHITE)
            file_color = self._get_dynamic_file_color(record.filename)
            line_color = LogColors.GRAY
            reset = LogColors.RESET

            f_time = f"{line_color}{time_str}{reset}"
            f_sep = f"{line_color}|{reset}"
            f_file = f"{file_color}{record.filename:<{self.FILE_COLUMN_WIDTH}}{reset}"
            f_lvl = f"{lvl_color}{record.levelname:<8}{reset}"
            f_msg = f"{lvl_color}{msg}{reset}"

            return f"{f_time} {f_sep} {f_file} {f_sep} {f_lvl} {f_sep} {f_msg}"
        else:
            return f"{time_str} | {record.filename:<{self.FILE_COLUMN_WIDTH}} | {record.levelname:<8} | {msg}"


def setup_universal_logger(config: LoggerConfig) -> logging.Logger:
    """
    Initializes and configures the universal logger, targeting the explicitly defined configuration parameters.
    """
    logger = logging.getLogger("awr_automation")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if not logger.hasHandlers():
        os.makedirs(config.log_dir, exist_ok=True)
        log_filepath = os.path.join(config.log_dir, config.log_name)

        with open(log_filepath, "w", encoding="utf-8") as f:
            f.write(f"LOG SESSION INITIALIZED: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
            f.write("-" * 60 + "\n")

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(ProfessionalFormatter(use_colors=config.use_colors))

        file_handler = logging.FileHandler(log_filepath, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(ProfessionalFormatter(use_colors=False))

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger


# Global instance fallback to maintain compatibility with legacy imports
# that expect a pre-configured logger without explicit dependency injection.
_default_logger_config = LoggerConfig(log_dir=default_paths.logs_dir)
logger = setup_universal_logger(_default_logger_config)


if __name__ == "__main__":
    import sys
    print("├── Starting standalone test sequence for logger.py")
    try:
        test_cfg = LoggerConfig(log_dir="./test_logs")
        test_logger = setup_universal_logger(test_cfg)
        test_logger.info("│   ├── Diagnostic test message: Information level.")
        test_logger.warning("│   ├── Diagnostic test message: Warning level.")
        print("└── Test execution sequence completed successfully")
    except Exception as ex:
        print(f"└── Test execution failed: {ex}")
        sys.exit(1)