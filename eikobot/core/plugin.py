"""
Eikobot plugins expose python fucntions
as callables directly to the Eikobot runtime.
"""
from typing import Callable, Optional, Union

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
