"""
The regex module contains bindings to pythons re module.
"""
import re

from eikobot.core.plugin import eiko_plugin


@eiko_plugin()
def match(regex: str, string: str) -> bool:
    """Returns a True if python re.match returns a result."""
    if re.match(regex, string) is not None:
        return True

    return False
