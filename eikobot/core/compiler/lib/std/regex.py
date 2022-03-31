import re

from eikobot.core.plugin import eiko_plugin


@eiko_plugin
def match(regex: str, string: str) -> bool:
    if re.match(regex, string) is not None:
        return True

    return False
