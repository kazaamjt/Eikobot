"""
Context hold variables, classes and more.
Used both by files/modules and fucntions.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Type, Union

from ... import logger
from ...errors import EikoCompilationError, EikoInternalError
from ...handlers import Handler
from ..decorator import index_decorator
from ..importlib import import_python_code
from ..token import Token
from .base_types import (
    EikoBaseType,
    EikoBool,
    EikoDictType,
    EikoFloat,
    EikoInt,
    EikoListType,
    EikoOptional,
    EikoPath,
    EikoStr,
    EikoType,
    EikoUnion,
    EikoUnset,
    eiko_none_object,
)
from .resource import ResourceDefinition
from .typedef import EikoTypeDef

if TYPE_CHECKING:
    from ..parser import Parser

_StorableTypes = Union[
    EikoBaseType, ResourceDefinition, Type[EikoBaseType], EikoType, Type[EikoType]
]
_builtins: dict[str, _StorableTypes] = {
    "int": EikoInt,
    "float": EikoFloat,
    "bool": EikoBool,
    "str": EikoStr,
    "Path": EikoPath,
    "None": eiko_none_object,
    "Union": EikoUnion,
    "Optional": EikoOptional,
    "list": EikoListType,
    "dict": EikoDictType,
    "index": index_decorator,
}


@dataclass
class LazyLoadModule:
    """A lazyLoadModule is meant to only be compiled when it is directly called."""

    context: "CompilerContext"
    parser: "Parser"
    import_path: list[str]

    def compile(self) -> "CompilerContext":
        """Imports plugins and compiles eiko code so the module can be used."""
        if not self.context.compiled:
            logger.debug(f"Importing module '{self.context.get_import_name()}'")
            for expr in self.parser.parse():
                expr.compile(self.context)

            import_python_code(
                self.import_path,
                self.parser.lexer.file_path,
                self.context,
            )
            self.context.flag_as_compiled()
        return self.context


class CompilerContext:
    """
    Context hold variables, classes and more.
    Used both by files/modules and functions.
    """

    def __init__(
        self,
        name: str,
        super_scope: Optional["CompilerContext"] = None,
        super_module: Optional["CompilerContext"] = None,
    ) -> None:
        self.name = name
        self.storage: dict[
            str,
            Union[_StorableTypes, "CompilerContext", LazyLoadModule, EikoUnset, None],
        ] = {}
        self.path: Path
        self.type = EikoType("eiko_internal_context")
        self.super = super_scope
        self.super_module = super_module
        self.compiled = False
        self.handlers: dict[str, Type[Handler]] = {}
        self.orphans: list[EikoBaseType] = []

        self.global_id_list: list[str]
        if self.super is not None:
            self.global_id_list = self.super.global_id_list
        elif self.super_module is not None:
            self.global_id_list = self.super_module.global_id_list
        else:
            self.global_id_list = []

    def flag_as_compiled(self) -> None:
        self.compiled = True

    def set_path(self, path: Path) -> None:
        self.path = path
        self.storage["__file__"] = EikoPath(path)

    def __repr__(self, indent: str = "") -> str:
        return_str = indent + f"Context '{self.name}': " + "{\n"
        extra_indent = indent + "    "
        for key, value in self.storage.items():
            if isinstance(value, CompilerContext):
                return_str += value.__repr__(extra_indent)
            elif isinstance(value, LazyLoadModule):
                pass
            elif isinstance(value, ResourceDefinition):
                return_str += value.printable(extra_indent)
            elif isinstance(value, EikoBaseType):
                extra_extra_indent = extra_indent + "    "
                return_str += f"{extra_indent}var '{key}':\n"
                return_str += extra_extra_indent + value.printable(extra_extra_indent)
                return_str += "\n"
            else:
                return_str += f"{extra_indent}{key}: {value}\n"

        return_str += indent + "}\n"
        return return_str

    def get(
        self, name: str, token: Optional[Token] = None
    ) -> Union[_StorableTypes, "CompilerContext", None]:
        """Get a value from this context or a super context."""
        value = self.storage.get(name)

        if isinstance(value, LazyLoadModule):
            value = value.compile()
            self.storage[name] = value
        elif value is None and self.super is not None:
            value = self.super.get(name, token)

        if value is None:
            value = _builtins.get(name)

        if isinstance(value, EikoUnset):
            raise EikoCompilationError(
                "Variable accessed before having been assignend a value.",
                token=token,
            )

        return value

    def shallow_get(
        self, name: str
    ) -> Union[_StorableTypes, "CompilerContext", EikoUnset, None]:
        """
        Shallow get only gets builtins and values local to the current scope.
        It is primarily for use by 'Set'.
        """
        value = self.storage.get(name)

        if isinstance(value, LazyLoadModule):
            value = value.compile()
        elif value is None:
            value = _builtins.get(name)

        return value

    def set(
        self,
        name: str,
        value: Union[_StorableTypes, "CompilerContext", EikoUnset],
        token: Optional[Token] = None,
    ) -> None:
        """Set a value. Throws an error if it's already set."""
        prev_value = self.shallow_get(name)
        if isinstance(prev_value, EikoUnset):
            if prev_value.type.inverse_type_check(value.type):
                constr = self.get(prev_value.type.name)
                if isinstance(constr, EikoTypeDef):
                    if isinstance(value, EikoBaseType):
                        value = constr.execute(value, token)
                    else:
                        raise EikoInternalError(
                            "Something went wrong trying to coerce a type to it's typedef.",
                            token=token,
                        )

            if not prev_value.type.type_check(value.type):
                raise EikoCompilationError(
                    f"Tried to assign value of type {value.type} "
                    f"to a variable declared as type {prev_value.type}.",
                    token=token,
                )

        elif prev_value is not None:
            raise EikoCompilationError(
                f"Illegal operation: Tried to reassign '{name}'.",
                token=token,
            )

        self.storage[name] = value
        self._connect_handler(name)

    def get_or_set_context(
        self, name: str, token: Optional[Token] = None
    ) -> "CompilerContext":
        """
        Either retrieve a context or create it if it doesn't exist.
        """
        context = self.get(name)
        if isinstance(context, CompilerContext):
            return context

        if context is None:
            new_context = CompilerContext(name, super_module=self)
            self.set(name, new_context)
            return new_context

        raise EikoCompilationError(
            f'Illegal operation: Tried to reassign "{name}".',
            token=token,
        )

    def get_subcontext(self, name: str) -> "CompilerContext":
        """
        Creates a new context, with the given context as its super context,
        but does not store the new context in the super context.
        """
        return CompilerContext(name, self)

    def register_handler(self, handler: Type[Handler]) -> None:
        """
        Adds a handler to the context for later retrieval.
        """
        prev_handler = self.handlers.get(handler.resource)
        if prev_handler is not None:
            raise EikoCompilationError(
                f"A handler for resource type '{handler.resource}' was already registered."
            )

        self.handlers[handler.resource] = handler
        self._connect_handler(handler.resource)

    def _connect_handler(self, name: str) -> None:
        handler = self.handlers.get(name)
        if handler is None:
            return

        resource = self.storage.get(name)
        if resource is None:
            return

        if not isinstance(resource, ResourceDefinition):
            raise EikoCompilationError(
                f"Tried to connect a handler to '{name}', which is not a resource."
            )

        logger.debug(
            f"Linking handler {handler} to resource '{self.get_import_name(include_main=True)}.{name}'"
        )
        resource.handler = handler

    def get_import_name(self, include_main: bool = False) -> str:
        """Constructs a name based on inherited contexts."""
        name = ""
        if self.name == "__main__" and not include_main:
            return name

        if self.super_module is not None:
            super_name = self.super_module.get_import_name()
            if super_name != "":
                name += super_name + "."

        return name + self.name


StorableTypes = Union[_StorableTypes, "CompilerContext"]
