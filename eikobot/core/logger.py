"""
The logging module is used to log messages in a consistent and unified way.
It gives access to print helper functions and custom progress bars.
"""
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

import colorama
from colorama import Fore

if TYPE_CHECKING:
    from .compiler.misc import Index


class LogLevel(Enum):
    """Enum class to indicate the loglevel."""

    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()


LOG_LEVEL = LogLevel.INFO
_LOG_LEVEL_SET = False
WARNINGS = 0


def init(log_level: LogLevel = LogLevel.INFO) -> None:
    """Initialize the console submodule"""
    global LOG_LEVEL  # pylint: disable=global-statement
    global _LOG_LEVEL_SET  # pylint: disable=global-statement
    if _LOG_LEVEL_SET:
        warning("eikobot.logger.init was already called before.")

    _LOG_LEVEL_SET = True
    LOG_LEVEL = log_level
    colorama.init()


def debug(*args: str, pre: str = "", **kwargs: Any) -> None:
    """Print a debug level message."""
    if LOG_LEVEL == LogLevel.DEBUG:
        print(pre + Fore.BLUE + "DEBUG" + Fore.RESET, *args, **kwargs)


def info(*args: str, pre: str = "", **kwargs: Any) -> None:
    """Print an info level message."""
    if LOG_LEVEL.value <= LogLevel.INFO.value:
        print(pre + Fore.GREEN + "INFO" + Fore.RESET, *args, **kwargs)


def warning(*args: str, pre: str = "", **kwargs: Any) -> None:
    """Print a warning."""
    global WARNINGS  # pylint: disable=global-statement
    WARNINGS += 1
    if LOG_LEVEL.value <= LogLevel.WARNING.value:
        print(pre + Fore.YELLOW + "WARNING" + Fore.RESET, *args, **kwargs)


def error(*args: str, pre: str = "", **kwargs: Any) -> None:
    """Print a big fat error."""
    print(pre + Fore.RED + "ERROR" + Fore.RESET, *args, **kwargs)


def print_error_trace(index: "Index") -> None:
    """Using a given index, creates a nice CLI trace."""
    print(f'    File "{index.file.absolute()}", line {index.line + 1}')
    with open(index.file, "r", encoding="utf-8") as f:
        line = f.readlines()[index.line]
        clean_line = line.lstrip()
        diff = len(line) - len(clean_line)
        print(" " * 8 + clean_line.strip("\n"))
        print(" " * 8 + (index.col - diff) * " " + "^")
