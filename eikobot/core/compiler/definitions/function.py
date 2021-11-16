from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

from .base_types import EikoBaseType

if TYPE_CHECKING:
    from ..parser import ExprAST
    from .context import CompilerContext


@dataclass
class FunctionArg:
    name: str
    type: str
    default_value: Optional[EikoBaseType] = None


class FunctionDefinition(EikoBaseType):
    def __init__(self) -> None:
        super().__init__("function")
        self.args: List[FunctionArg] = []
        self.body: List["ExprAST"] = []

    def add_arg(self, arg: FunctionArg) -> None:
        self.args.append(arg)

    def add_body_expr(self, expr: "ExprAST") -> None:
        self.body.append(expr)

    def execute(self, contex: "CompilerContext") -> None:
        for expr in self.body:
            expr.compile(contex)
