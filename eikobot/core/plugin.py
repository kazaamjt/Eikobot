from typing import Any, Callable

from .compiler.definitions.base_types import EikoBaseType


def eiko_plugin(function: Callable[..., Any]) -> Callable[..., EikoBaseType]:
    function.eiko_plugin = True  # type: ignore

    return function
