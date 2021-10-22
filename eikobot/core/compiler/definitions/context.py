from typing import Dict, Optional, Type, Union

from ..errors import EikoCompilationError
from ..token import Token
from .base_types import EikoBaseType, EikoBool, EikoFloat, EikoInt, EikoStr
from .resource import ResourceDefinition

StorableTypes = Union[EikoBaseType, ResourceDefinition, Type[EikoBaseType]]


class CompilerContext:
    def __init__(
        self, name: str, super_scope: Optional["CompilerContext"] = None
    ) -> None:
        self.name = name
        self.storage: Dict[str, StorableTypes] = {
            "int": EikoInt,
            "float": EikoFloat,
            "bool": EikoBool,
            "str": EikoStr,
        }
        self.super = super_scope

    def get(self, name: str) -> Optional[StorableTypes]:
        value = self.storage.get(name)
        if value is None and self.super is not None:
            value = self.super.get(name)

        return value

    def set(
        self,
        name: str,
        value: StorableTypes,
        token: Optional[Token] = None,
    ) -> None:
        prev_value = self.get(name)
        if prev_value is not None:
            raise EikoCompilationError(
                f"Illegal operation: Tried to reassign {name}.",
                token=token,
            )

        self.storage[name] = value
