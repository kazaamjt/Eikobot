"""
While real functions don't exist in the eiko language,
constructors and plugins do, and they need some kind of representation.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Type, Union

from ...plugin import EikoPluginException, EikoPluginTyping
from ..errors import EikoCompilationError, EikoPluginError
from ..token import Token
from .base_types import (
    INDEXABLE_TYPES,
    EikoBaseType,
    EikoResource,
    EikoType,
    PassedArg,
    to_eiko,
    to_eiko_type,
    to_py,
)
from .typedef import EikoTypeDef

if TYPE_CHECKING:
    from ..parser import ExprAST
    from .context import CompilerContext, StorableTypes

EikoFunctionType = EikoType("function")


@dataclass
class ConstructorArg:
    """Representation of a required constructor argument."""

    name: str
    type: EikoType
    default_value: Optional[EikoBaseType] = None


class ConstructorDefinition(EikoBaseType):
    """Internal representation of an Eikobot constructor."""

    def __init__(
        self, class_name: str, name: str, execution_context: "CompilerContext"
    ) -> None:
        super().__init__(EikoFunctionType)
        self.class_name = class_name
        self.name = name
        self.args: Dict[str, ConstructorArg] = {}
        self.body: List["ExprAST"] = []
        self.execution_context = execution_context
        self.index_def: List[str] = []

    def printable(self, _: str = "") -> str:
        raise NotImplementedError

    def add_arg(self, arg: ConstructorArg) -> None:
        self.args[arg.name] = arg

    def add_body_expr(self, expr: "ExprAST") -> None:
        self.body.append(expr)

    def execute(
        self,
        callee_token: Token,
        positional_args: List[PassedArg],
        keyword_args: Dict[str, PassedArg],
    ) -> EikoResource:
        """
        Executes a function call based on a premade constructor spec.
        """
        if len(positional_args) + len(keyword_args) > len(self.args) - 1:
            raise EikoCompilationError(
                "Too many arguments given to function call.",
                token=callee_token,
            )

        handled_args: Dict[str, EikoBaseType] = {}
        self_arg = list(self.args.values())[0]
        resource = EikoResource(self_arg.type)
        handled_args[self_arg.name] = resource
        self._handle_args(
            handled_args, positional_args, keyword_args, self.execution_context
        )

        for arg_name, arg in self.args.items():
            if arg_name not in handled_args:
                if arg.default_value is None:
                    raise EikoCompilationError(
                        f"Argument '{arg_name}' for callable '{callee_token.content}' requires a value.",
                        token=callee_token,
                    )

                handled_args[arg_name] = arg.default_value

        context = self.execution_context.get_subcontext(f"{self.name}-execution")
        for arg_name, value in handled_args.items():
            context.set(arg_name, value)

        for expr in self.body:
            expr.compile(context)

        res_index = ""

        for property_name in self.index_def:
            if property_name == self.class_name:
                continue
            index_prop = resource.properties.get(property_name)
            if not isinstance(index_prop, INDEXABLE_TYPES):
                # Pass a token so we can have a trace.
                raise EikoCompilationError(
                    f"Property '{property_name}' of '{self.class_name}' is not an indexable type."
                )

            res_index += "-" + index_prop.index()

        resource.set_index(res_index[1:])

        return resource

    def _handle_args(
        self,
        handled_args: Dict[str, EikoBaseType],
        positional_args: List[PassedArg],
        keyword_args: Dict[str, PassedArg],
        context: "CompilerContext",
    ) -> None:
        for passed_arg, arg in zip(positional_args, list(self.args.values())[1:]):
            if not passed_arg.value.type_check(arg.type):
                # Try to coerce the type
                if arg.type.inverse_type_check(passed_arg.value.type):
                    type_constr = context.get(arg.type.name)
                    if isinstance(type_constr, EikoTypeDef):
                        passed_arg.value = type_constr.execute(
                            passed_arg.value, passed_arg.token
                        )
                    else:
                        raise EikoCompilationError(
                            f"Argument '{arg.name}' expected value of type '{arg.type}', "
                            f"but got value of type '{passed_arg.value.type}'.",
                            token=passed_arg.token,
                        )
                else:
                    raise EikoCompilationError(
                        f"Argument '{arg.name}' expected value of type '{arg.type}', "
                        f"but got value of type '{passed_arg.value.type}'.",
                        token=passed_arg.token,
                    )

            handled_args[arg.name] = passed_arg.value

        for arg_name, passed_arg in keyword_args.items():
            positional_value = handled_args.get(arg_name)
            if positional_value is not None:
                raise EikoCompilationError(
                    f"'{self.name}()' got multiple values for argument '{arg_name}'."
                )

            kw_arg = self.args.get(arg_name)
            if kw_arg is None:
                raise EikoCompilationError(
                    f"'{self.name}()' has no argument '{arg_name}'."
                )

            if not passed_arg.value.type_check(kw_arg.type):
                raise EikoCompilationError(
                    f"Argument '{kw_arg.name}' expected value of type '{kw_arg.type}', "
                    f"but got value of type '{passed_arg.value.type}'.",
                    token=passed_arg.token,
                )

            handled_args[arg_name] = passed_arg.value

    def truthiness(self) -> bool:
        raise NotImplementedError


EikoPluginType = EikoType("plugin")


@dataclass
class PluginArg:
    name: str
    py_type: Type[Union[EikoBaseType, bool, float, int, str, list, dict]]


class PluginDefinition(EikoBaseType):
    """
    Internal representation of a python plugin
    that can be called from the Eikobot language.
    """

    def __init__(
        self,
        body: EikoPluginTyping,
        return_type: Type[EikoBaseType],
        identifier: str,
        module: str,
    ) -> None:
        super().__init__(EikoPluginType)
        self.body = body
        self.return_type = to_eiko_type(return_type)
        self._body_return_type = return_type
        self.args: List[PluginArg] = []
        self.identifier = identifier
        self.module = module

    def printable(self, _: str = "") -> str:
        return f"Plugin '{self.identifier}'"

    def add_arg(self, arg: PluginArg) -> None:
        self.args.append(arg)

    def execute(
        self, args: List["ExprAST"], context: "CompilerContext", token: Optional[Token]
    ) -> Optional[EikoBaseType]:
        """Execute the stored function and coerces types."""

        stable_args = []
        for i, arg in enumerate(args):
            stable_args.append(self._handle_arg(arg, context, self.args[i]))

        try:
            val = self.body(*stable_args)
        except EikoPluginException as e:
            raise EikoPluginError(str(e), token=token) from e
        except Exception as e:
            raise EikoPluginError(
                f"An unhandled exception occured while executing plugin '{self.identifier}'",
                token=token,
                python_exception=e,
            ) from e

        return to_eiko(val)

    def _handle_arg(
        self, arg: "ExprAST", context: "CompilerContext", required_arg: PluginArg
    ) -> Union[EikoBaseType, bool, float, int, str]:
        compiled_arg = arg.compile(context)
        if compiled_arg is None:
            raise EikoCompilationError(
                f"Plugin '{self.module}.{self.identifier}' arg '{required_arg.name}' expects a value "
                f"but expression did not result in a suitable value.",
                token=arg.token,
            )
        if issubclass(required_arg.py_type, EikoBaseType):
            converted_arg: Union[
                "StorableTypes", bool, float, int, str, Path
            ] = compiled_arg
        else:
            try:
                converted_arg = to_py(compiled_arg)
            except ValueError as e:
                raise EikoCompilationError(
                    "Failed to convert to python type when passing to plugin.",
                    token=arg.token,
                ) from e

        if not isinstance(converted_arg, required_arg.py_type):
            raise EikoCompilationError(
                f"Plugin '{self.module}.{self.identifier}' arg '{required_arg.name}' expects an argument "
                f"of type '{required_arg.py_type.__name__}', but instead got '{compiled_arg.type}'.",
                token=arg.token,
            )

        return converted_arg  # type: ignore

    def truthiness(self) -> bool:
        raise NotImplementedError
