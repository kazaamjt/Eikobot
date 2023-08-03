"""
Typedef definitions are executable functions of sorts.
They can alias types and even put restrictions on them.
"""
from typing import TYPE_CHECKING, Optional, Union

from ...errors import EikoCompilationError
from .._token import Token
from .base_types import (
    BuiltinTypes,
    EikoBaseType,
    EikoBool,
    EikoFloat,
    EikoInt,
    EikoPath,
    EikoStr,
    EikoType,
)

if TYPE_CHECKING:
    from .._parser import ExprAST
    from .context import CompilerContext


class EikoTypeDef(EikoBaseType):
    """Simple custom type definitions."""

    def __init__(
        self,
        name: str,
        super_type: Union[EikoType, "EikoTypeDef"],
        condition: Optional["ExprAST"],
        context: "CompilerContext",
    ) -> None:
        self.name = name
        self.condition = condition
        self.context = context
        self.super = super_type
        if isinstance(super_type, EikoType):
            self.type = EikoType(name, super_type, self)
        else:
            self.type = EikoType(name, super_type.type, self)
        super().__init__(self.type)

    def printable(self, _: str = "") -> str:
        return f"TypeDef '{self.name}' redefining '{self.type.super}'"

    def truthiness(self) -> bool:
        raise NotImplementedError

    def execute(self, arg: EikoBaseType, arg_token: Optional[Token]) -> BuiltinTypes:
        """
        Cast a value to a type and make sure it fits the given condition expression.
        """
        if arg.type.type_check(self.type):
            raise EikoCompilationError(
                f"Type '{self.name}' requires '{self.type.name}' but was passed '{arg.type.name}'.",
                token=arg_token,
            )

        if isinstance(self.super, EikoType):
            base_constructor = self.context.get(self.super.name)
            if base_constructor in (EikoBool, EikoFloat, EikoInt, EikoPath, EikoStr):
                arg = base_constructor(arg.get_value(), self.type)  # type: ignore

        elif isinstance(self.super, EikoTypeDef):
            arg = self.super.execute(arg, arg_token)
            arg.type = EikoType(self.name, arg.type)

        if self.condition is not None:
            condition_context = self.context.get_subcontext(f"{self.name}-typedef")
            condition_context.set("self", arg)
            res = self.condition.compile(condition_context)
            if not isinstance(res, EikoBaseType) or not res.truthiness():
                raise EikoCompilationError(
                    f"Value '{arg.get_value()}' did not meet typedef condition for '{self.name}'.",
                    token=arg_token,
                )

        if isinstance(arg, (EikoBool, EikoFloat, EikoInt, EikoPath, EikoStr)):
            return arg

        raise NotImplementedError
