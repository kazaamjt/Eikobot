"""
Resource and ResourceProperty class definitions.
Resource is the base building block of the eiko language model.
"""
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Dict, Optional

from pydantic import BaseModel

from ...handlers import Handler
from .base_types import EikoBaseType, EikoType

if TYPE_CHECKING:
    from .._parser import ResourceDefinitionAST
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


class EikoResourceDefinition(EikoBaseType):
    """Internal representation of a resource definition."""

    def __init__(
        self,
        name: str,
        expr: "ResourceDefinitionAST",
        default_constructor: "ConstructorDefinition",
        properties: Dict[str, ResourceProperty],
        instance_type: EikoType,
    ) -> None:
        super().__init__(EikoResourceDefinitionType)
        self.expr = expr
        self.token = expr.token
        self.name = name
        self.instance_type = instance_type
        self.default_constructor = default_constructor
        self.default_constructor.parent = self
        self.properties = properties
        self.index_def = [list(properties.keys())[0]]
        self.handler: Optional[type[Handler]] = None
        self.linked_basemodel: Optional[type[EikoBaseModel]] = None

    def printable(self, indent: str = "") -> str:
        return_str = f"{indent}Resource Definition '{self.name}'"
        if self.type.super is not None:
            return_str += f"('{self.type.super.name}')"
        return_str += ": " + "{\n"
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
    __eiko_linked_definition__: ClassVar[EikoResourceDefinition]

    @classmethod
    def link(cls, resource_cls: EikoResourceDefinition) -> None:
        """Links a resource to a BaseModel."""
        cls.__eiko_linked_definition__ = resource_cls
        resource_cls.linked_basemodel = cls

    @classmethod
    def get_resource_name(cls) -> str:
        return cls.__eiko_resource__
