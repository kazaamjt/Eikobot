"""
Resource and ResourceProperty class definitions.
Resource is the base building block of the eiko language model.
"""
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union

from .base_types import EikoBaseType, EikoPromise, EikoResource, EikoType

if TYPE_CHECKING:
    from ...handlers import Handler
    from .._parser import ResourceDefinitionAST, TypeExprAST
    from .._token import Token
    from .base_model import EikoBaseModel
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
    type_expr: "TypeExprAST | None" = None


@dataclass
class EikoPromiseDefinition:
    """
    Internal representation of a promise constructor.
    """

    name: str
    type: EikoType

    def execute(self, callee_token: "Token", parent: EikoResource) -> EikoPromise:
        return EikoPromise(
            self.name,
            self.type,
            callee_token,
            parent,
        )


EikoResourceDefinitionType = EikoType("ResourceDefinition")
PropertiesDict = dict[str, Union[ResourceProperty, EikoPromiseDefinition]]


class EikoResourceDefinition(EikoBaseType):
    """Internal representation of a resource definition."""

    def __init__(
        self,
        expr: "ResourceDefinitionAST",
        default_constructor: "ConstructorDefinition",
        properties: PropertiesDict,
        promises: list[EikoPromiseDefinition],
    ) -> None:
        super().__init__(EikoResourceDefinitionType)
        self.expr = expr
        self.name = expr.name
        self.instance_type: EikoType = expr.type
        self.default_constructor = default_constructor
        self.default_constructor.parent = self
        self.properties: PropertiesDict = properties
        self.index_def = [list(properties.keys())[0]]
        self.promises: list[EikoPromiseDefinition] = promises
        self.handler: Optional[type["Handler"]] = None
        self.linked_basemodel: Optional[type["EikoBaseModel"]] = None

    def printable(self, indent: str = "") -> str:
        return_str = f"{indent}Resource Definition '{self.name}'"
        if self.type.super is not None:
            return_str += f"('{self.type.super.name}')"
        return_str += ": " + "{\n"

        for value in self.properties.values():
            return_str += indent + "    "
            if isinstance(value, EikoPromiseDefinition):
                return_str += "promise "
            return_str += f"{value.name}: {value.type}\n"

        return_str += indent + "}\n"

        return return_str

    def truthiness(self) -> bool:
        raise NotImplementedError
