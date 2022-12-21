"""
Decorators enhance an eiko resource definition in some way.
"""
from typing import Callable, Type, Union

from ..errors import EikoCompilationError
from ._token import Token
from .definitions._resource import EikoResourceDefinition
from .definitions.base_types import EikoBaseType, EikoList, EikoStr, EikoType

decorator_type = EikoType("Decorator")


class EikoDecorator(EikoBaseType):
    """
    Decorators enhance a resource definition in some way.
    """

    def __init__(
        self,
        identifier: str,
        func: Callable[[EikoResourceDefinition, list, Token], None],
        arg_spec: list[Type],
    ) -> None:
        super().__init__(decorator_type)
        self.identifier = identifier
        self.func = func
        # Make arg_Spec automatic, like for plugins?
        self.arg_spec = arg_spec

    def execute(
        self, res_def: EikoResourceDefinition, args: list, call_token: Token
    ) -> None:
        """Execute the decorator on the given resource."""
        if len(args) != len(self.arg_spec):
            raise EikoCompilationError(
                f"Decorator {self.identifier}, expects {len(self.arg_spec)} arguments, "
                f"but got {len(args)}.",
                token=call_token,
            )

        i = 0
        for arg, spec in zip(args, self.arg_spec):
            if not isinstance(arg, spec):
                raise EikoCompilationError(
                    f"Argument {i} of decorator {self.identifier} expected type {spec}.",
                    token=call_token,
                )
            i += 1

        self.func(res_def, args, call_token)

    def get_value(self) -> Union[None, bool, float, int, str]:
        raise NotImplementedError

    def printable(self, _: str = "") -> str:
        raise NotImplementedError

    def truthiness(self) -> bool:
        raise NotImplementedError


def _index_decorator(
    res_def: EikoResourceDefinition, args: list, call_token: Token
) -> None:
    index: EikoList = args[0]
    new_index: list[str] = [res_def.name]
    for arg in index.elements:
        if not isinstance(arg, EikoStr):
            raise EikoCompilationError(
                "Index decorator expects a list of strings to be passed.",
                token=call_token,
            )
        new_index.append(arg.value)

    res_def.index_def = new_index


index_decorator = EikoDecorator("index", _index_decorator, [EikoList])
