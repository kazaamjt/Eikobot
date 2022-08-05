"""
Base types are used by the compiler internally to represent Objects,
strings, integers, floats, and booleans, in a way that makes sense to the compiler.
"""
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, Union

from ..errors import EikoCompilationError
from ..token import Token

if TYPE_CHECKING:
    from .context import StorableTypes


class EikoType:
    """
    The EikoType is used for typechecking.
    It is a property of every object and performs type checking functions.
    """

    type: "EikoType"

    def __init__(self, name: str, super_type: Optional["EikoType"] = None) -> None:
        self.name = name
        self.super = super_type

    def type_check(self, expected_type: "EikoType") -> bool:
        """Recursivly type checks."""
        if self.name == expected_type.name:
            return True

        if expected_type.super is not None:
            return self.type_check(expected_type.super)

        return False

    def get_top_level_type(self) -> "EikoType":
        """Returns the toplevel super type."""
        if self.super is None:
            return self

        return self.super

    def __repr__(self) -> str:
        return self.name


EikoType.type = EikoType("Type")
eiko_base_type = EikoType("Object")


class EikoUnion(EikoType):
    """Represents an Eiko Union type, which combines 2 or more types."""

    def __init__(
        self,
        name: str,
        types: List[EikoType],
        super_type: None = None,
    ) -> None:
        self.types = types
        super().__init__(name, super_type)

    def type_check(self, expected_type: EikoType) -> bool:
        """Recursivly type checks."""
        for _type in self.types:
            if _type.type_check(expected_type):
                return True

        return False


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

    def get_value(self) -> Union[None, bool, float, int, str]:
        raise NotImplementedError

    def printable(self, indent: str = "") -> str:
        raise NotImplementedError

    def truthiness(self) -> bool:
        raise NotImplementedError

    def type_check(self, expected_type: EikoType) -> bool:
        return expected_type.type_check(self.type)


_eiko_none_type = EikoType("None")


class EikoOptional(EikoType):
    """Eiko optional means a value can be None."""

    def __init__(self, optional_type: EikoType) -> None:
        super().__init__("None", eiko_base_type)
        self.optional_type = optional_type

    def type_check(self, expected_type: "EikoType") -> bool:
        if self.name == expected_type.name:
            return True

        return expected_type.type_check(self.optional_type)

    def __repr__(self) -> str:
        return f"Optinal[{self.optional_type.name}]"


class EikoNone(EikoBaseType):
    """Represents the None Value in the Eiko Language."""

    type = _eiko_none_type

    def __init__(self, eiko_type: EikoType = _eiko_none_type) -> None:
        super().__init__(eiko_type)
        self.value = None

    def get_value(self) -> None:
        return None

    def printable(self, _: str = "") -> str:
        return "None"

    def truthiness(self) -> bool:
        return False


eiko_none_object = EikoNone()
_eiko_int_type = EikoType("int")


class EikoInt(EikoBaseType):
    """Represents an integer in the Eiko language."""

    type = _eiko_int_type

    def __init__(self, value: int, eiko_type: EikoType = _eiko_int_type) -> None:
        super().__init__(eiko_type)
        self.value = value

    def get_value(self) -> int:
        return self.value

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

    def get_value(self) -> float:
        return self.value

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

    def get_value(self) -> bool:
        return self.value

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

    def get_value(self) -> str:
        return self.value

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

    def get_value(self) -> Union[bool, float, int, str]:
        raise NotImplementedError

    def set(self, name: str, value: "StorableTypes", token: Token) -> None:
        """Set the value of a property, if the value wasn't already assigned."""
        if not isinstance(value, EikoBaseType):
            raise EikoCompilationError(
                f"Property {name} of class {self.type} "
                f"cannot be assigned the given value.",
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
            _repr += ",\n"

        _repr += indent + "}"

        return _repr

    def truthiness(self) -> bool:
        return True


BuiltinTypes = Union[EikoBool, EikoFloat, EikoInt, EikoStr]


def to_eiko_type(cls: Optional[Type]) -> Type[EikoBaseType]:
    """
    Takes a python type and returns it's eikobot compatible type.
    If said type exists.
    """
    if cls is None:
        return EikoNone

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

    if value is None:
        return eiko_none_object

    raise ValueError


def to_py(value: Any) -> Union[bool, float, int, str]:
    """Takes an Eikobot type and tries to coerce it to a python type."""
    if isinstance(value, (EikoBool, EikoFloat, EikoInt, EikoStr)):
        return value.value

    raise ValueError
