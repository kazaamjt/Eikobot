from dataclasses import dataclass
from typing import Dict, Optional

from ..token import Token
from ..errors import EikoCompilationError
from .base_types import EikoBaseType
from .function import FunctionDefinition


@dataclass
class ResourceProperty:
    name: str
    type: str
    default_value: Optional[EikoBaseType] = None
    token: Optional[Token] = None


class ResourceDefinition(EikoBaseType):
    def __init__(
        self, name: str, properties: Dict[str, ResourceProperty], token: Token
    ) -> None:
        super().__init__("resource")
        self.token = token
        self.name = name
        self.properties: Dict[str, ResourceProperty] = properties
        self.constructors: Dict[str, FunctionDefinition] = {}

    def add_constructor(self, name: str, func_def: FunctionDefinition) -> None:
        self.constructors[name] = func_def

    def get(self, name: str) -> FunctionDefinition:
        constructor = self.constructors.get(name)
        if constructor is None:
            raise EikoCompilationError(
                f"No such constructor: {name} for Resource {self.name}."
            )

        return constructor
