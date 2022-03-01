"""
Resource and ResourceProperty class definitions.
Resource is the base building block of the eiko language model.
"""
from dataclasses import dataclass
from typing import Dict, Optional, Union

from ..errors import EikoCompilationError
from ..token import Token
from .base_types import EikoBaseType
from .function import FunctionDefinition


@dataclass
class ResourceProperty:
    name: str
    type: str
    default_value: Optional[EikoBaseType] = None


class ResourceDefinition(EikoBaseType):
    def __init__(self, name: str, token: Token) -> None:
        super().__init__(name)
        self.token = token
        self.name = name
        self.properties: Dict[str, ResourceProperty] = {}
        self.constructors: Dict[str, FunctionDefinition] = {}

    def printable(self) -> Union[Dict, int, str]:
        raise NotImplementedError

    def add_property(self, prop: ResourceProperty) -> None:
        self.properties[prop.name] = prop

    def add_constructor(self, name: str, func_def: FunctionDefinition) -> None:
        self.constructors[name] = func_def

    def get(self, name: str) -> FunctionDefinition:
        constructor = self.constructors.get(name)
        if constructor is None:
            raise EikoCompilationError(
                f"No such constructor: {name} for Resource {self.name}."
            )

        return constructor
