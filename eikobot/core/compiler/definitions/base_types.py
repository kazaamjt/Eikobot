"""
Base types are used by the compiler internally to represent Objects,
strings, integers, floats, and booleans, in a way that makes sense to the compiler.
"""
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional, Type, Union

from ..errors import EikoCompilationError
from ..token import Token

if TYPE_CHECKING:
    from .context import StorableTypes


@dataclass
class EikoType:
    """
    The EikoType is used for typechecking.
    It is a property of every object and performs type checking functions.
    """

    name: str
    super: Optional["EikoType"] = None

    def type_check(self, expected_type: "EikoType") -> bool:
        """Recursivly type checks."""
        if self == expected_type:
            return True

        if self.super is not None:
            return self.super.type_check(expected_type)

        return False

    def get_top_level_type(self) -> "EikoType":
        """Returns the toplevel super type."""
        if self.super is None:
            return self

        return self.super

    def __repr__(self) -> str:
        return self.name


eiko_base_type = EikoType("Object")


class EikoBaseType:
    """
    The base type represents all objects, it is inherited from by all other types.
    It shouldn't show up naturally anywhere though.
    """

    type = eiko_base_type

    def __init__(self, eiko_type: EikoType) -> None:
        self.type = eiko_type

    def get(self, name: str) -> Optional["EikoBaseType"]:
        raise EikoCompilationError(
            f"Object of type {self.type} has no property {name}."
        )

    def printable(self, indent: str = "") -> str:
        raise NotImplementedError

    def truthiness(self) -> bool:
        raise NotImplementedError

    def type_check(self, expected_type: EikoType) -> bool:
        return self.type.type_check(expected_type)


_eiko_int_type = EikoType("int")


class EikoInt(EikoBaseType):
    """Represents an integer in the Eiko language."""

    type = _eiko_int_type

    def __init__(self, value: int, eiko_type: EikoType = _eiko_int_type) -> None:
        super().__init__(eiko_type)
        self.value = value

    def printable(self, _: str = "") -> str:
        return f"{self.type} {self.value}"

    def truthiness(self) -> bool:
        return bool(self.value)


_eiko_float_type = EikoType("float")


class EikoFloat(EikoBaseType):
    """Represents a float in the Eiko language."""

    type = _eiko_float_type

    def __init__(self, value: float, eiko_type: EikoType = _eiko_float_type) -> None:
        super().__init__(eiko_type)
        self.value = value

    def printable(self, _: str = "") -> str:
        return f"{self.type} {self.value}"

    def truthiness(self) -> bool:
        return bool(self.value)


EikoNumber = Union[EikoInt, EikoFloat]

_eiko_bool_type = EikoType("bool")


class EikoBool(EikoBaseType):
    """Represents a boolean in the Eiko language."""

    type = _eiko_bool_type

    def __init__(self, value: bool, eiko_type: EikoType = _eiko_bool_type) -> None:
        super().__init__(eiko_type)
        self.value = value

    def printable(self, _: str = "") -> str:
        return f"{self.type} {self.value}"

    def truthiness(self) -> bool:
        return self.value


_eiko_str_type = EikoType("str")


class EikoStr(EikoBaseType):
    """Represents a string in the Eiko language."""

    type = _eiko_str_type

    def __init__(self, value: str, eiko_type: EikoType = _eiko_str_type) -> None:
        super().__init__(eiko_type)
        self.value = value

    def printable(self, _: str = "") -> str:
        return f'{self.type} "{self.value}"'

    def truthiness(self) -> bool:
        return bool(self.value)


class EikoResource(EikoBaseType):
    """Represents a custom resource in the Eiko language."""

    def __init__(self, eiko_type: EikoType) -> None:
        super().__init__(eiko_type)
        self.properties: Dict[str, EikoBaseType] = {}

    def get(self, name: str) -> Optional[EikoBaseType]:
        return self.properties.get(name)

    def set(self, name: str, value: "StorableTypes", token: Token) -> None:
        """Set the value of a property, if the value wasn't already assigned."""
        if not isinstance(value, EikoBaseType):
            raise EikoCompilationError(
                f"Unable to assign property {name} of class {self.type} "
                f"cannot be assigned given value.",
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

    def truthiness(self) -> bool:
        return True


BuiltinTypes = Union[EikoBool, EikoFloat, EikoInt, EikoStr]


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
