from colorama import Fore

from eikobot.core.plugin import eiko_plugin


@eiko_plugin
def debug_msg(msg: str) -> None:
    """Writes a message to the console."""
    print(Fore.BLUE + "DEBUG_MSG" + Fore.RESET, msg)
