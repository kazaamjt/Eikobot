"""
This module is used for eikobot testing.
"""
from eikobot.core.plugin import eiko_plugin


@eiko_plugin()
def add_string(string_1: str, string_2: str) -> str:
    """Adds 2 strings together."""
    return string_1 + string_2
