from typing import Callable, Union

from .compiler.definitions.base_types import EikoBaseType


def eiko_plugin(
    function: Callable[..., Union[bool, float, int, str, EikoBaseType]]
) -> Callable[..., Union[bool, float, int, str, EikoBaseType]]:
    function.eiko_plugin = True  # type: ignore

    return function
