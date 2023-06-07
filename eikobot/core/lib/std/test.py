"""
This module is used for eikobot testing.
"""
from eikobot.core.plugin import EikoPluginException, eiko_plugin


@eiko_plugin()
def add_string(string_1: str, string_2: str) -> str:
    """Adds 2 strings together."""
    return string_1 + string_2


@eiko_plugin()
def test_raise_exception() -> None:
    raise EikoPluginException("This plugins shows that Plugin exceptions work.")


@eiko_plugin()
def test_python_exception() -> None:
    raise ValueError("A python exception to test the plugin exception handling.")
