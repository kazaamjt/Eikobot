"""
Base types are used by the compiler internally to represent Objects,
strings, integers, floats, and booleans, in a way that makes sense to the compiler.
"""
from typing import TYPE_CHECKING, Dict, Optional, Union

from ..errors import EikoCompilationError
from ..token import Token

if TYPE_CHECKING:
    from .context import StorableTypes


class EikoBaseType:
    """
    The base type represents all types, it is inherited from by all other types.
    It shouldn't show up naturally anywhere though and is purely virtual.
    """

    name = "EikoObject"

    def __init__(self, eiko_type: str) -> None:
        self.type = eiko_type

    def get(self, name: str) -> Optional["EikoBaseType"]:
        raise EikoCompilationError(
            f"Object of type {self.type} has no property {name}."
        )

    def printable(self) -> Union[Dict, int, str]:
        raise NotImplementedError


class EikoInt(EikoBaseType):
    """
    Represents an integer in the Eiko language.
    """

    name = "int"

    def __init__(self, value: int) -> None:
        super().__init__(self.name)
        self.value = value

    def printable(self) -> int:
        return self.value


class EikoFloat(EikoBaseType):
    """
    Represents a float in the Eiko language.
    """

    name = "float"

    def __init__(self, value: float) -> None:
        super().__init__(self.name)
        self.value = value

    def printable(self) -> str:
        return str(self.value)


EikoNumber = Union[EikoInt, EikoFloat]


class EikoBool(EikoBaseType):
    """
    Represents a boolean in the Eiko language.
    """

    name = "bool"

    def __init__(self, value: bool) -> None:
        super().__init__(self.name)
        self.value = value

    def printable(self) -> str:
        return str(self.value)


class EikoStr(EikoBaseType):
    """
    Represents a string in the Eiko language.
    """

    name = "str"

    def __init__(self, value: str) -> None:
        super().__init__(self.name)
        self.value = value

    def printable(self) -> str:
        return self.value


class EikoResource(EikoBaseType):
    """
    Represents a custom resource in the Eiko language.
    """

    def __init__(self, eiko_type: str) -> None:
        super().__init__(eiko_type)
        self.properties: Dict[str, EikoBaseType] = {}

    def get(self, name: str) -> Optional[EikoBaseType]:
        return self.properties.get(name)

    def set(self, name: str, value: "StorableTypes", token: Token) -> None:
        """Set the value of a property, if the value wasn't already assigned."""
        if not isinstance(value, EikoBaseType):
            raise EikoCompilationError(
                f"Unable to assign property {name} of class {self.type} "
                f"cannot be assigned given vlaue.",
                token=token,
            )

        prop = self.properties.get(name)
        if prop is not None:
            raise EikoCompilationError(
                "Attempted to reassign a property that was already assigned.",
                token=token,
            )

        self.properties[name] = value

    def printable(self) -> Dict:
        return {
            f"[{val.type}] {name}": val.printable()
            for name, val in self.properties.items()
        }
