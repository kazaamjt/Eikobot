"""
Eikobot plugins expose python fucntions
as callables directly to the Eikobot runtime.
"""
from typing import Callable, Optional, Union

from . import human_readable, machine_readable
from .compiler.definitions.base_types import EikoBaseType

EikoPluginTyping = Callable[..., Union[None, bool, float, int, str, EikoBaseType]]


def eiko_plugin(alias: Optional[str] = None) -> Callable:
    """Tags a function as an Eikobot plugin with alias."""

    def _eiko_plugin(function: EikoPluginTyping) -> EikoPluginTyping:
        """Tags a function as an Eikobot plugin."""
        function.eiko_plugin = True  # type: ignore
        function.alias = alias  # type: ignore

        return function

    return _eiko_plugin


class EikoPluginException(Exception):
    """
    If something goes wrong inside a plugin, this error should be thrown.
    """


@eiko_plugin("type")
def eiko_type(
    obj: EikoBaseType,
) -> str:
    """
    Returns the type of a an eiko object as a string.
    """
    return obj.type.name


@eiko_plugin("human_readable")
def eiko_human_readable(number: int) -> str:
    """
    plugin wrapper for core function human_readable
    """
    return human_readable(number)


@eiko_plugin("machine_readable")
def eiko_machine_readable(number: str) -> int:
    """
    plugin wrapper for core function machine_readable
    """
    return machine_readable(number)
