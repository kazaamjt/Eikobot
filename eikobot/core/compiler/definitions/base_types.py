"""
Base types are used by the compiler internally to represent Objects,
strings, integers, floats, and booleans, in a way that makes sense to the compiler.
"""
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    Union,
)

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

    def __str__(self) -> str:
        return self.name


@dataclass
class EikoUnset:
    """
    Special type, allowing for forward declarations.
    """

    type: EikoType


EikoType.type = EikoType("Type")
eiko_base_type = EikoType("Object")


class EikoUnion(EikoType):
    """Represents an Eiko Union type, which combines 2 or more types."""

    def __init__(
        self,
        name: str,
        types: List[EikoType],
    ) -> None:
        self.types = types
        super().__init__(name)

    def type_check(self, expected_type: EikoType) -> bool:
        """Recursivly type checks."""

        if isinstance(expected_type, EikoUnion):
            for _type in expected_type.types:
                if not self.type_check(_type):
                    return False
            return True

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

    def get(self, name: str, token: Optional[Token] = None) -> "EikoBaseType":
        raise EikoCompilationError(
            f"Object of type {self.type} has no property {name}.",
            token=token,
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
        if expected_type is _eiko_none_type:
            return True

        return expected_type.type_check(self.optional_type)

    def __repr__(self) -> str:
        return f"Optional[{self.optional_type.name}]"


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


BuiltinTypes = Union[EikoBool, EikoFloat, EikoInt, EikoStr]


class EikoResource(EikoBaseType):
    """Represents a custom resource in the Eiko language."""

    def __init__(self, eiko_type: EikoType) -> None:
        super().__init__(eiko_type)
        self.properties: Dict[str, EikoBaseType] = {}

    def get(self, name: str, token: Optional[Token] = None) -> EikoBaseType:
        value = self.properties.get(name)
        if value is None:
            raise EikoCompilationError(
                "Tried to access a property that does not exist.",
                token=token,
            )

        return value

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


class EikoListType(EikoType):
    """Represents an Eiko Union type, which combines 2 or more types."""

    def __init__(self, element_type: EikoType) -> None:
        super().__init__(f"List[{element_type.name}]")
        self.element_type = element_type

    def type_check(self, expected_type: "EikoType") -> bool:
        if isinstance(expected_type, EikoListType):
            return self.element_type.type_check(expected_type.element_type)

        return False


_builtin_function_type = EikoType("builtin_function", eiko_base_type)


@dataclass
class PassedArg:
    """A passed arg is a compiled expression passed as an arg."""

    token: Token
    value: EikoBaseType


@dataclass
class BuiltinFunctionArg:
    name: str
    type: EikoType


class EikoBuiltinFunction(EikoBaseType):
    """
    Built in functions are typically convenience functions.
    They cannot be user generated.
    """

    def __init__(
        self,
        identifier: str,
        args: List[BuiltinFunctionArg],
        body: Callable[..., Optional[EikoBaseType]],
    ) -> None:
        super().__init__(_builtin_function_type)
        self.identifier = identifier
        self.args = args
        self.body = body

    def execute(
        self, callee_token: Token, args: List[PassedArg]
    ) -> Optional[EikoBaseType]:
        """Execute the builtin function."""
        if len(args) != len(self.args):
            raise EikoCompilationError(
                "Too many arguments given to function call.",
                token=callee_token,
            )

        validated_args: List[EikoBaseType] = []
        for passed_arg, expected_arg in zip(args, self.args):
            if not expected_arg.type.type_check(passed_arg.value.type):
                raise EikoCompilationError(
                    f"Argument '{expected_arg.name}' must be of type '{expected_arg.type}', "
                    f"but got '{passed_arg.value.type}'",
                    token=passed_arg.token,
                )
            validated_args.append(passed_arg.value)

        return self.body(*validated_args)

    def truthiness(self) -> bool:
        raise NotImplementedError


class EikoList(EikoBaseType):
    """Represents a list of objects in the Eiko language."""

    def __init__(
        self,
        element_type: EikoType,
        elements: Optional[List[EikoBaseType]] = None,
    ) -> None:
        super().__init__(EikoListType(element_type))
        if elements is None:
            self.elements: List[EikoBaseType] = []
        else:
            self.elements = elements

        self.append_func = EikoBuiltinFunction(
            "append",
            [BuiltinFunctionArg("element", element_type)],
            body=self.append,
        )

    def append(self, element: EikoBaseType) -> None:
        self.elements.append(element)

    def update_typing(self, new_type: EikoListType) -> None:
        self.type = new_type
        self.append_func = EikoBuiltinFunction(
            "append",
            [BuiltinFunctionArg("element", new_type.element_type)],
            body=self.append,
        )

    def get(self, name: str, token: Optional[Token] = None) -> "EikoBaseType":
        if name == "append":
            return self.append_func

        return super().get(name, token)

    def get_index(self, index: int) -> Optional[EikoBaseType]:
        try:
            return self.elements[index]
        except IndexError:
            return None

    def get_value(self) -> Union[bool, float, int, str]:
        raise NotImplementedError

    def printable(self, indent: str = "") -> str:
        extra_indent = indent + "    "
        _repr = "[\n"
        for val in self.elements:
            _repr += extra_indent
            _repr += val.printable(extra_indent)
            _repr += ",\n"

        _repr += indent + "]"
        return _repr

    def truthiness(self) -> bool:
        return bool(self.elements)


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
