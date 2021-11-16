from typing import TYPE_CHECKING, Dict, Optional, Union

from ..errors import EikoCompilationError
from ..token import Token

if TYPE_CHECKING:
    from .context import StorableTypes


class EikoBaseType:

    name = "EikoObject"

    def __init__(self, eiko_type: str) -> None:
        self.type = eiko_type

    def get(self, name: str) -> Optional["EikoBaseType"]:
        raise EikoCompilationError(
            f"Object of type {self.type} has no property {name}."
        )


class EikoInt(EikoBaseType):

    name = "int"

    def __init__(self, value: int) -> None:
        super().__init__(self.name)
        self.value = value


class EikoFloat(EikoBaseType):

    name = "float"

    def __init__(self, value: float) -> None:
        super().__init__(self.name)
        self.value = value


EikoNumber = Union[EikoInt, EikoFloat]


class EikoBool(EikoBaseType):

    name = "bool"

    def __init__(self, value: bool) -> None:
        super().__init__(self.name)
        self.value = value


class EikoStr(EikoBaseType):

    name = "str"

    def __init__(self, value: str) -> None:
        super().__init__(self.name)
        self.value = value


class EikoResource(EikoBaseType):
    def __init__(self, eiko_type: str) -> None:
        super().__init__(eiko_type)
        self.properties: Dict[str, EikoBaseType] = {}

    def get(self, name: str) -> Optional[EikoBaseType]:
        return self.properties.get(name)

    def set(self, name: str, value: "StorableTypes", token: Token) -> None:
        if not isinstance(value, EikoBaseType):
            raise EikoCompilationError(
                f"Unable to assign property {name} of class {self.type} "
                f"cannot be assigned given vlaue.",
                token=token,
            )

        prop = self.properties.get(name)
        if prop is not None:
            raise EikoCompilationError(
                "Attempted to reassign value to a variable that was already assigned.",
                token=token,
            )

        self.properties[name] = value
