from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

from .base_types import EikoBaseType

if TYPE_CHECKING:
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

    def add_arg(self, arg: FunctionArg) -> None:
        self.args.append(arg)

    def execute(self, contex: "CompilerContext") -> None:
        pass
