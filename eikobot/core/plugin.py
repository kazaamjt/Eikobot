"""
Eikobot plugins expose python fucntions
as callables directly to the Eikobot runtime.
"""
from typing import Callable, Union

from .compiler.definitions.base_types import EikoBaseType


def eiko_plugin(
    function: Callable[..., Union[None, bool, float, int, str, EikoBaseType]]
) -> Callable[..., Union[None, bool, float, int, str, EikoBaseType]]:
    """Tags a function as an Eikobot plugin."""
    function.eiko_plugin = True  # type: ignore

    return function
