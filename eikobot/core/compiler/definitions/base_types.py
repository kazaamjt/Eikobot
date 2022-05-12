"""
Base types are used by the compiler internally to represent Objects,
strings, integers, floats, and booleans, in a way that makes sense to the compiler.
"""
from typing import TYPE_CHECKING, Any, Dict, Optional, Type, Union

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
    type = "EikoObject"

    def __init__(self, eiko_type: str) -> None:
        self.type = eiko_type

    def get(self, name: str) -> Optional["EikoBaseType"]:
        raise EikoCompilationError(
            f"Object of type {self.type} has no property {name}."
        )

    def printable(self, indent: str = "") -> str:
        raise NotImplementedError


class EikoInt(EikoBaseType):
    """
    Represents an integer in the Eiko language.
    """

    name = "int"
    type = "int"

    def __init__(self, value: int) -> None:
        super().__init__(self.name)
        self.value = value

    def printable(self, _: str = "") -> str:
        return f"int '{self.value}'"


class EikoFloat(EikoBaseType):
    """
    Represents a float in the Eiko language.
    """

    name = "float"
    type = "float"

    def __init__(self, value: float) -> None:
        super().__init__(self.name)
        self.value = value

    def printable(self, _: str = "") -> str:
        return f"float '{self.value}'"


EikoNumber = Union[EikoInt, EikoFloat]


class EikoBool(EikoBaseType):
    """
    Represents a boolean in the Eiko language.
    """

    name = "bool"
    type = "bool"

    def __init__(self, value: bool) -> None:
        super().__init__(self.name)
        self.value = value

    def printable(self, _: str = "") -> str:
        return f"bool '{self.value}'"


class EikoStr(EikoBaseType):
    """
    Represents a string in the Eiko language.
    """

    name = "str"
    type = "str"

    def __init__(self, value: str) -> None:
        super().__init__(self.name)
        self.value = value

    def printable(self, _: str = "") -> str:
        return f"str '{self.value}'"


class EikoResource(EikoBaseType):
    """
    Represents a custom resource in the Eiko language.
    """

    type = "EikoResource"

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

    def printable(self, indent: str = "") -> str:
        extra_indent = indent + "    "
        _repr = "{\n"
        for name, val in self.properties.items():
            _repr += extra_indent
            _repr += f"{val.type} '{name}': "
            _repr += val.printable(extra_indent)

        _repr += "\n" + indent + "}"

        return _repr


def to_eiko_type(cls: Type) -> Type[EikoBaseType]:
    """
    Takes a python type and returns it's eikobot compatible type.
    If said type exists.
    """
    if issubclass(cls, EikoBaseType):
        return cls

    if cls == bool:
        return EikoBool

    if cls == float:
        return EikoFloat

    if cls == int:
        return EikoInt

    if cls == str:
        return EikoStr

    raise ValueError


def to_eiko(value: Any) -> EikoBaseType:
    """Takes a python value and tries to coerce it to an Eikobot type."""
    if isinstance(value, bool):
        return EikoBool(value)

    if isinstance(value, float):
        return EikoFloat(value)

    if isinstance(value, int):
        return EikoInt(value)

    if isinstance(value, str):
        return EikoStr(value)

    if isinstance(value, EikoBaseType):
        return value

    raise ValueError


def to_py(value: Any) -> Union[bool, float, int, str]:
    """Takes an Eikobot type and tries to coerce it to a python type."""
    if isinstance(value, (EikoBool, EikoFloat, EikoInt, EikoStr)):
        return value.value

    raise ValueError
