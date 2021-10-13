from typing import List, Optional

from .eiko_types import EikoBaseType


class ResourceProperty:
    def __init__(
        self, name: str, prop_type: str, default_value: Optional[EikoBaseType]
    ) -> None:
        self.name = name
        self.type = prop_type
        self.default_value = default_value


class ResourceDefinition(EikoBaseType):
    def __init__(self, name: str, properties: List[ResourceProperty]) -> None:
        super().__init__("resource")
        self.name = name
        self.properties = properties


class CompilerContext:
    def __init__(self, name: str) -> None:
        self.name = name
        self.registered_types = ["int", "float", "bool", "str", "resource"]
