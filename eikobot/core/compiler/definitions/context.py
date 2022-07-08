"""
Context hold variables, classes and more.
Used both by files/modules and fucntions.
"""
from typing import Dict, List, Optional, Type, Union

from ..errors import EikoCompilationError
from ..token import Token
from .base_types import (
    EikoBaseType,
    EikoBool,
    EikoFloat,
    EikoInt,
    EikoResource,
    EikoStr,
    EikoType,
)
from .resource import ResourceDefinition

_StorableTypes = Union[EikoBaseType, ResourceDefinition, Type[EikoBaseType]]
_builtins = {
    "int": EikoInt,
    "float": EikoFloat,
    "bool": EikoBool,
    "str": EikoStr,
}


class CompilerContext:
    """
    Context hold variables, classes and more.
    Used both by files/modules and fucntions.
    """

    def __init__(
        self,
        name: str,
        super_scope: Optional["CompilerContext"] = None,
    ) -> None:
        self.name = name
        self.storage: Dict[str, Union[_StorableTypes, "CompilerContext", None]] = {}
        self.type = EikoType("eiko_internal_context")
        self.super = super_scope
        self.assigned: Dict[str, EikoResource] = {}
        self.extra_contexts: List["CompilerContext"] = []

    def __repr__(self, indent: str = "") -> str:
        return_str = indent + f"Context '{self.name}': " + "{\n"
        extra_indent = indent + "    "
        for key, value in self.storage.items():
            if isinstance(value, CompilerContext):
                return_str += value.__repr__(extra_indent)
            elif isinstance(value, EikoBaseType):
                return_str += (
                    f"{extra_indent}var {key}: {value.printable(extra_indent)}\n"
                )
            else:
                return_str += f"{extra_indent}{key}: {value}\n"

        return_str += indent + "}\n"
        return return_str

    def get(self, name: str) -> Union[_StorableTypes, "CompilerContext", None]:
        """Get a value from this context or a super context."""
        value = self.storage.get(name)
        if value is None and self.super is not None:
            value = self.super.get(name)

        if value is None:
            value = _builtins.get(name)

        if value is None and self.extra_contexts:
            for context in self.extra_contexts:
                value = context.get(name)
                if value is not None:
                    return value

        return value

    def shallow_get(self, name: str) -> Union[_StorableTypes, "CompilerContext", None]:
        """
        Shallow get only gets builtins and values local to the current scope.
        It is primarily for use by 'Set'.
        """
        value = self.storage.get(name)

        if value is None:
            value = _builtins.get(name)

        return value

    def set(
        self,
        name: str,
        value: Union[_StorableTypes, "CompilerContext"],
        token: Optional[Token] = None,
    ) -> None:
        """Set a value. Throws an error if it's already set."""
        prev_value = self.shallow_get(name)
        if prev_value is not None:
            raise EikoCompilationError(
                f'Illegal operation: Tried to reassign "{name}".',
                token=token,
            )

        if isinstance(value, EikoResource):
            self.assigned[name] = value

        self.storage[name] = value

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
            new_context = CompilerContext(name)
            self.set(name, new_context)
            return new_context

        raise EikoCompilationError(
            f'Illegal operation: Tried to reassign "{name}".',
            token=token,
        )


StorableTypes = Union[_StorableTypes, "CompilerContext"]
