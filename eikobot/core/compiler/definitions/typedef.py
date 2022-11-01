"""
Typedef definitions are executable functions of sorts.
They can alias types and even put restrictions on them.
"""
from typing import TYPE_CHECKING, Optional

from ..errors import EikoCompilationError
from ..token import Token
from .base_types import (
    BuiltinTypes,
    EikoBaseType,
    EikoBool,
    EikoFloat,
    EikoInt,
    EikoStr,
    EikoType,
)

if TYPE_CHECKING:
    from ..parser import ExprAST
    from .context import CompilerContext


class EikoTypeDef(EikoBaseType):
    """Simple custom type definitions."""

    def __init__(
        self,
        name: str,
        super_type: EikoType,
        condition: Optional["ExprAST"],
        context: "CompilerContext",
    ) -> None:
        self.name = name
        self.type = EikoType(name, super_type)
        self.condition = condition
        self.context = context
        super().__init__(self.type)

    def printable(self, _: str = "") -> str:
        return f"TypeDef '{self.name}' redefining '{self.type.super}'"

    def truthiness(self) -> bool:
        raise NotImplementedError

    def execute(self, arg: EikoBaseType, arg_token: Token) -> BuiltinTypes:
        """
        Cast a value to a type and make sure it fits the given condition expression.
        """
        if arg.type_check(self.type):
            raise EikoCompilationError(
                f"Type '{self.name}' requires '{self.type.name}' but was passed '{arg.type.name}'.",
                token=arg_token,
            )

        if self.condition is not None:
            condition_context = self.context.get_subcontext(f"{self.name}-typedef")
            condition_context.set("self", arg)
            res = self.condition.compile(condition_context)
            if not isinstance(res, EikoBaseType) or not res.truthiness():
                raise EikoCompilationError(
                    f"Value '{arg.get_value()}' did not meet typedef condition for '{self.name}'.",
                    token=arg_token,
                )

        base_type = self.type.get_top_level_type()
        base_constructor = self.context.get(base_type.name)
        if base_constructor in (EikoBool, EikoFloat, EikoInt, EikoStr):
            return base_constructor(arg.get_value(), self.type)  # type: ignore

        raise NotImplementedError(arg_token)
