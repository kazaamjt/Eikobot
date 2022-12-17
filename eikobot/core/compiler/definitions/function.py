"""
While real functions don't exist in the eiko language,
constructors and plugins do, and they need some kind of representation.
"""
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Type, Union

from ...errors import EikoCompilationError, EikoPluginError
from ...plugin import EikoPluginException, EikoPluginTyping
from .._token import Token
from .base_types import (
    INDEXABLE_TYPES,
    EikoBaseType,
    EikoResource,
    EikoType,
    EikoUnset,
    PassedArg,
    PyTypes,
    to_eiko,
    to_eiko_type,
)
from .typedef import EikoTypeDef

if TYPE_CHECKING:
    from .._parser import ExprAST
    from ._resource import ResourceDefinition
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

    def __init__(self, name: str, execution_context: "CompilerContext") -> None:
        super().__init__(EikoFunctionType)
        self.parent: "ResourceDefinition"
        self.name = name
        self.args: dict[str, ConstructorArg] = {}
        self.body: list["ExprAST"] = []
        self.execution_context = execution_context
        self.index_def: list[str] = []

    def printable(self, _: str = "") -> str:
        raise NotImplementedError

    def add_arg(self, arg: ConstructorArg) -> None:
        self.args[arg.name] = arg

    def add_body_expr(self, expr: "ExprAST") -> None:
        self.body.append(expr)

    def execute(  # pylint: disable=too-many-locals,too-many-branches
        self,
        callee_token: Token,
        positional_args: list[PassedArg],
        keyword_args: dict[str, PassedArg],
    ) -> EikoResource:
        """
        Executes a function call based on a premade constructor spec.
        """
        if len(positional_args) + len(keyword_args) > len(self.args) - 1:
            raise EikoCompilationError(
                "Too many arguments given to function call. "
                f"Expected {len(self.args) - 1}, "
                f"got {len(positional_args) + len(keyword_args)}.",
                token=callee_token,
            )

        handled_args: dict[str, EikoBaseType] = {}
        self_arg = list(self.args.values())[0]
        resource = EikoResource(self.parent)
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

        context = self.execution_context.get_subcontext(
            f"{self.parent.name}.{self.name}"
        )
        for prop in self.parent.properties.values():
            resource.populate_property(prop.name, prop.type)

        for arg_name, value in handled_args.items():
            context.set(arg_name, value)

        for expr in self.body:
            expr.compile(context)

        for prop in self.parent.properties.values():
            res_prop = resource.properties.get(prop.name)
            if isinstance(res_prop, EikoUnset):
                raise EikoCompilationError(
                    f"Property '{self.parent.name}.{prop.name}' was not set in the constructor.",
                    token=callee_token,
                )

        res_index = self.parent.name
        for property_name in self.index_def:
            if property_name == self.parent.name:
                continue
            prop_name_split = property_name.split(".")
            index_prop: Union[EikoBaseType, EikoUnset, None] = resource
            for prop_name in prop_name_split:
                if isinstance(index_prop, EikoResource):
                    index_prop = index_prop.properties.get(prop_name)
                else:
                    raise EikoCompilationError(
                        f"Failed to create index using property '{property_name}': "
                        f"No property '{prop_name}'.",
                        token=self.parent.token,
                    )

            if not isinstance(index_prop, INDEXABLE_TYPES):
                # Pass a token so we can have a trace.
                raise EikoCompilationError(
                    f"Property '{property_name}' of '{self.parent.name}' is not an indexable type.",
                    token=self.parent.token,
                )

            res_index += "-" + index_prop.index()

        resource.set_index(res_index)
        if resource.index() in context.global_id_list:
            raise EikoCompilationError(
                f"A resource of type '{self.parent.name}' with index "
                f"'{resource.index()}' was already created.",
                token=callee_token,
            )

        context.global_id_list.append(resource.index())

        return resource

    def _handle_args(
        self,
        handled_args: dict[str, EikoBaseType],
        positional_args: list[PassedArg],
        keyword_args: dict[str, PassedArg],
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


class DefaultValueNotSet:
    """Indicates no default value was set."""

    def __init__(self) -> None:
        pass


@dataclass
class PluginArg:
    """Class representing an argument in a plugin call."""

    name: str
    py_type: Union[Type[EikoBaseType], Type[PyTypes]]
    default_value: Union[PyTypes, DefaultValueNotSet] = DefaultValueNotSet()


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
        self.args: list[PluginArg] = []
        self.identifier = identifier
        self.module = module

    def printable(self, _: str = "") -> str:
        return f"Plugin '{self.identifier}'"

    def add_arg(self, arg: PluginArg) -> None:
        self.args.append(arg)

    def execute(
        self, args: list["ExprAST"], context: "CompilerContext", token: Optional[Token]
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
            converted_arg: Union["StorableTypes", PyTypes] = compiled_arg
        else:
            if isinstance(compiled_arg, EikoBaseType):
                converted_arg = compiled_arg.to_py()
            else:
                raise EikoCompilationError(
                    "Failed to convert to python type when passing to plugin.",
                    token=arg.token,
                )

        if not isinstance(converted_arg, required_arg.py_type):
            raise EikoCompilationError(
                f"Plugin '{self.module}.{self.identifier}' arg '{required_arg.name}' expects an argument "
                f"of type '{required_arg.py_type.__name__}', but instead got '{compiled_arg.type}'.",
                token=arg.token,
            )

        return converted_arg  # type: ignore

    def truthiness(self) -> bool:
        raise NotImplementedError
