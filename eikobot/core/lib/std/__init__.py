"""
The Eiko standard library contains various quality of life
plugins and resources.
"""
from colorama import Fore

from eikobot.core.plugin import eiko_plugin
from eikobot.core.types import EikoBaseType, EikoStr


@eiko_plugin()
def debug_msg(msg: str) -> None:
    """Writes a message to the console."""
    print(Fore.BLUE + "DEBUG_MSG" + Fore.RESET, msg)


@eiko_plugin("print")
def eiko_print(obj: EikoBaseType) -> None:
    """Prints messages and objects to the console."""
    if isinstance(obj, EikoStr):
        print("PRINT " + obj.value)

    print("PRINT " + obj.printable())
