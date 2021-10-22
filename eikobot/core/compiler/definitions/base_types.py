from typing import Dict, Optional, Union

from ..errors import EikoCompilationError


class EikoBaseType:
    def __init__(self, eiko_type: str) -> None:
        self.type = eiko_type

    def get(self, name: str) -> Optional["EikoBaseType"]:
        raise EikoCompilationError(
            f"Object of type {self.type} has no property {name}."
        )


class EikoInt(EikoBaseType):
    def __init__(self, value: int) -> None:
        super().__init__("int")
        self.value = value


class EikoFloat(EikoBaseType):
    def __init__(self, value: float) -> None:
        super().__init__("float")
        self.value = value


EikoNumber = Union[EikoInt, EikoFloat]


class EikoBool(EikoBaseType):
    def __init__(self, value: bool) -> None:
        super().__init__("bool")
        self.value = value


class EikoStr(EikoBaseType):
    def __init__(self, value: str) -> None:
        super().__init__("str")
        self.value = value


class EikoResource(EikoBaseType):
    def __init__(self, eiko_type: str, properties: Dict[str, EikoBaseType]) -> None:
        super().__init__(eiko_type)
        self.properties = properties

    def get(self, name: str) -> Optional[EikoBaseType]:
        return self.properties.get(name)
