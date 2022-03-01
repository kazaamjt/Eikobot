import re

from eikobot.core.plugin import eiko_plugin
from eikobot.core.types import EikoBool, EikoStr


@eiko_plugin
def match(regex: EikoStr, string: EikoStr) -> EikoBool:
    if re.match(regex.value, string.value) is not None:
        return EikoBool(True)

    return EikoBool(False)
