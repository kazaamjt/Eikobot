from typing import Dict, Optional, Type, Union

from ..errors import EikoCompilationError
from ..token import Token
from .base_types import EikoBaseType, EikoBool, EikoFloat, EikoInt, EikoStr
from .resource import ResourceDefinition

_StorableTypes = Union[EikoBaseType, ResourceDefinition, Type[EikoBaseType]]


class CompilerContext:
    def __init__(
        self,
        name: str,
        super_scope: Optional["CompilerContext"] = None,
    ) -> None:
        self.name = name
        self.storage: Dict[str, Union[_StorableTypes, "CompilerContext", None]] = {
            "int": EikoInt,
            "float": EikoFloat,
            "bool": EikoBool,
            "str": EikoStr,
        }
        self.type = "ModuleContext"
        self.super = super_scope

    def __repr__(self, indent: str = "") -> str:
        return_str = indent + "{\n"
        extra_indent = indent + "    "
        for key, value in self.storage.items():
            if isinstance(value, CompilerContext):
                return_str += value.__repr__(extra_indent)
            else:
                return_str += f"{extra_indent}{key}: {value}\n"

        return_str += indent + "}\n"
        return return_str

    def get(self, name: str) -> Union[_StorableTypes, "CompilerContext", None]:
        value = self.storage.get(name)
        if value is None and self.super is not None:
            value = self.super.get(name)

        return value

    def set(
        self,
        name: str,
        value: Union[_StorableTypes, "CompilerContext"],
        token: Optional[Token] = None,
    ) -> None:
        prev_value = self.get(name)
        if prev_value is not None:
            raise EikoCompilationError(
                f"Illegal operation: Tried to reassign {name}.",
                token=token,
            )

        self.storage[name] = value


StorableTypes = Union[_StorableTypes, "CompilerContext"]
