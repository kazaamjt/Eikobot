"""
Resource and ResourceProperty class definitions.
Resource is the base building block of the eiko language model.
"""
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Optional

from ..token import Token
from .base_types import EikoBaseType, EikoType, eiko_base_type

if TYPE_CHECKING:
    from .function import ConstructorDefinition


@dataclass
class ResourceProperty:
    """
    Internal representation of a resource property for constructors.
    It does not verify wether the default value given is the correct type.
    """

    name: str
    type: EikoType
    default_value: Optional[EikoBaseType] = None


class ResourceDefinition(EikoBaseType):
    """Internal representation of a resource definition."""

    def __init__(
        self,
        name: str,
        token: Token,
        default_constructor: "ConstructorDefinition",
        properties: Dict[str, ResourceProperty],
    ) -> None:
        super().__init__(EikoType(name, eiko_base_type))
        self.token = token
        self.name = name
        self.default_constructor = default_constructor
        self.properties = properties
        self.index_def = [list(properties.keys())[0]]

    def printable(self, _: str = "") -> str:
        return f"Resource Definition '{self.name}'"

    def truthiness(self) -> bool:
        raise NotImplementedError
