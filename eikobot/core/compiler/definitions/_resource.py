"""
Resource and ResourceProperty class definitions.
Resource is the base building block of the eiko language model.
"""
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Dict, Optional

from pydantic import BaseModel

from ...handlers import Handler
from .._token import Token
from .base_types import EikoBaseType, EikoObjectType, EikoType

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


EikoResourceDefinitionType = EikoType("ResourceDefinition")


class ResourceDefinition(EikoBaseType):
    """Internal representation of a resource definition."""

    def __init__(
        self,
        name: str,
        token: Token,
        default_constructor: "ConstructorDefinition",
        properties: Dict[str, ResourceProperty],
    ) -> None:
        super().__init__(EikoResourceDefinitionType)
        self.token = token
        self.name = name
        self.instance_type = EikoType(name, EikoObjectType)
        self.default_constructor = default_constructor
        self.default_constructor.parent = self
        self.properties = properties
        self.index_def = [list(properties.keys())[0]]
        self.handler: Optional[type[Handler]] = None
        self.linked_basemodel: Optional[type[EikoBaseModel]] = None

    def printable(self, indent: str = "") -> str:
        return_str = f"{indent}Resource Definition '{self.name}': " + "{\n"
        for value in self.properties.values():
            return_str += f"{indent}    {value.name}: {value.type.name}\n"

        return_str += indent + "}\n"

        return return_str

    def truthiness(self) -> bool:
        raise NotImplementedError


class EikoBaseModel(BaseModel):
    """
    Used to handily convert eikoclasses to python classes
    and back.
    """

    __eiko_resource__: ClassVar[str]
    __eiko_linked_definition__: ClassVar[ResourceDefinition]

    @classmethod
    def link(cls, resource_cls: ResourceDefinition) -> None:
        """Links a resource to a BaseModel."""
        cls.__eiko_linked_definition__ = resource_cls
        resource_cls.linked_basemodel = cls

    @classmethod
    def get_resource_name(cls) -> str:
        return cls.__eiko_resource__
