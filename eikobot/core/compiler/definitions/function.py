"""
While real functions don't exist in the eiko language,
constructors and plugins do, and they need some kind of representation.
"""
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Type, Union

from ..errors import EikoCompilationError
from .base_types import EikoBaseType, to_eiko, to_eiko_type, to_py

if TYPE_CHECKING:
    from ..parser import ExprAST
    from .context import CompilerContext, StorableTypes


@dataclass
class FunctionArg:
    """Representation of a required FunctionArg."""

    name: str
    type: str
    default_value: Optional[EikoBaseType] = None


class FunctionDefinition(EikoBaseType):
    """Internal representation of an Eikobot function."""

    def __init__(self) -> None:
        super().__init__("function")
        self.args: List[FunctionArg] = []
        self.body: List["ExprAST"] = []

    def printable(self) -> Union[Dict, int, str]:
        raise NotImplementedError

    def add_arg(self, arg: FunctionArg) -> None:
        self.args.append(arg)

    def add_body_expr(self, expr: "ExprAST") -> None:
        self.body.append(expr)

    def execute(self, contex: "CompilerContext") -> None:
        for expr in self.body:
            expr.compile(contex)


@dataclass
class PluginArg:
    name: str
    py_type: Type[Union[EikoBaseType, bool, float, int, str]]


class PluginDefinition(EikoBaseType):
    """
    Internal representation of a python plugin
    that can be called from the Eikobot language.
    """

    def __init__(
        self,
        body: Callable[..., Union[None, bool, float, int, str, EikoBaseType]],
        return_type: Type[EikoBaseType],
        identifier: str,
        module: str,
    ) -> None:
        super().__init__("plugin")
        self.body = body
        self.return_type = to_eiko_type(return_type)
        self._body_return_type = return_type
        self.args: List[PluginArg] = []
        self.identifier = identifier
        self.module = module

    def printable(self) -> str:
        return f"PLUGIN {self.identifier}"

    def add_arg(self, arg: PluginArg) -> None:
        self.args.append(arg)

    def execute(
        self, args: List["ExprAST"], dummy_context: "CompilerContext"
    ) -> Optional[EikoBaseType]:
        """Execute the stored function and coerce types."""

        stable_args = []
        for i, arg in enumerate(args):
            stable_args.append(self._handle_arg(arg, dummy_context, self.args[i]))

        val = self.body(*stable_args)

        return to_eiko(val)

    def _handle_arg(
        self, arg: "ExprAST", dummy_context: "CompilerContext", required_arg: PluginArg
    ) -> Union[EikoBaseType, bool, float, int, str]:
        compiled_arg = arg.compile(dummy_context)
        if compiled_arg is None:
            raise EikoCompilationError(
                f"Plugin '{self.module}.{self.name}' arg '{required_arg.name}' expects a value "
                f"but expression did not result in a suitable value.",
                token=arg.token,
            )
        if issubclass(required_arg.py_type, EikoBaseType):
            converted_arg: Union["StorableTypes", bool, float, int, str] = compiled_arg
        else:
            try:
                converted_arg = to_py(compiled_arg)
            except ValueError as e:
                raise EikoCompilationError(
                    "Failed to convert to python type when apssing to plugin.",
                    token=arg.token,
                ) from e

        if not isinstance(converted_arg, required_arg.py_type):
            raise EikoCompilationError(
                f"Plugin '{self.module}.{self.name}' arg '{required_arg.name}' expects an argument "
                f"of type '{required_arg.py_type.__name__}', but instead got '{compiled_arg.type}'.",
                token=arg.token,
            )

        return converted_arg  # type: ignore
