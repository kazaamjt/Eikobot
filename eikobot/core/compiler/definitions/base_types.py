# pylint: disable=too-many-lines
"""
Base types are used by the compiler internally to represent Objects,
strings, integers, floats, and booleans, in a way that makes sense to the compiler.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Iterator,
    Optional,
    Type,
    TypeVar,
    Union,
)

from pydantic import BaseModel, ValidationError

from ...errors import (
    EikoCompilationError,
    EikoError,
    EikoInternalError,
    EikoUnresolvedPromiseError,
)
from .._token import Token

if TYPE_CHECKING:
    from ...handlers import HandlerContext
    from ._resource import EikoResourceDefinition
    from .base_model import EikoBaseModel
    from .context import StorableTypes
    from .typedef import EikoTypeDef


class EikoType:
    """
    The EikoType is used for typechecking.
    It is a property of every object and performs type checking functions.
    """

    type: "EikoType"

    def __init__(
        self,
        name: str,
        super_type: Optional["EikoType"] = None,
        typedef: Optional["EikoTypeDef"] = None,
    ) -> None:
        self.name = name
        self.super = super_type
        self.typedef = typedef

    @classmethod
    def convert(cls, _: "BuiltinTypes") -> "EikoBaseType":
        raise ValueError

    def type_check(self, expected_type: "EikoType") -> bool:
        """
        Recursivly type checks.

        NOTE: in most cases it should be value.type.type_check(expected_type)
        and not the other way around.
        """
        if self == eiko_any_type:
            return True

        if self.name == expected_type.name:
            return True

        if self.super is not None:
            return self.super.type_check(expected_type)

        if isinstance(expected_type, EikoUnion):
            for expected_sub_type in expected_type.types:
                if self.type_check(expected_sub_type):
                    return True

        if isinstance(expected_type, EikoOptional):
            return self.type_check(expected_type.optional_type)

        return False

    def inverse_type_check(self, expected_type: "EikoType") -> bool:
        """Checks if a given type is the same or a super type of this type."""
        if self.name == expected_type.name:
            return True

        if expected_type.super is not None:
            return self.inverse_type_check(expected_type.super)

        return False

    def get_top_level_type(self) -> "EikoType":
        """Returns the toplevel super type."""
        if self.super is None:
            return self

        return self.super

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.__repr__()


@dataclass
class EikoUnset:
    """
    Special type, allowing for forward declarations.
    """

    type: EikoType

    @staticmethod
    def get_value() -> str:
        return "Unset"

    @staticmethod
    def printable(_: str) -> str:
        return "Unset"

    def to_py(self) -> None:
        return None


eiko_any_type = EikoType("Any")
EikoType.type = EikoType("Type")
EikoObjectType = EikoType("Object")


def type_list_to_type(types: list[EikoType]) -> EikoType:
    """Turns a list of Eiko types in to a single usable type."""
    if len(types) == 0:
        return EikoType("")

    if len(types) == 1:
        _type = types[0]
    else:
        union_name = "Union["
        for sub_type in types:
            union_name += sub_type.name + ","
        _type = EikoUnion(union_name[:-1] + "]", types)

    return _type


class EikoUnion(EikoType):
    """Represents an Eiko Union type, which combines 2 or more types."""

    def __init__(
        self,
        name: str,
        types: list[EikoType],
    ) -> None:
        self.types = types
        super().__init__(name)

    def type_check(self, expected_type: EikoType) -> bool:
        """Recursivly type checks."""

        if isinstance(expected_type, EikoUnion):
            for _type in self.types:
                if not expected_type.type_check(_type):
                    return False
            return True

        for _type in self.types:
            if _type.type_check(expected_type):
                return True

        return False


PyTypes = Union[None, bool, float, int, str, dict, list, Path, BaseModel]


class EikoBaseType:
    """
    The base type represents all objects, it is inherited from by all other object classes.
    It shouldn't show up naturally anywhere though.
    """

    type = EikoObjectType

    def __init__(self, eiko_type: EikoType) -> None:
        self.type = eiko_type

    def get(self, name: str, token: Optional[Token] = None) -> "EikoBaseType":
        raise EikoCompilationError(
            f"Object of type '{self.type}' has no property '{name}'.",
            token=token,
        )

    @classmethod
    def convert(cls, _: "BuiltinTypes") -> "EikoBaseType":
        raise ValueError

    def get_value(self) -> PyTypes:
        raise NotImplementedError

    def printable(self, indent: str = "") -> str:
        raise NotImplementedError

    def truthiness(self) -> bool:
        raise NotImplementedError

    def index(self) -> str:
        raise NotImplementedError

    def to_py(self) -> Union[PyTypes, "EikoPromise"]:
        raise NotImplementedError

    def iterate(self, token: Token) -> Iterator["EikoBaseType"]:
        raise EikoCompilationError(
            f"Object of type '{self.type}' is not iterable.",
            token=token,
        )


EikoNoneType = EikoType("None")


class EikoOptional(EikoType):
    """Eiko optional means a value can be None."""

    def __init__(self, optional_type: EikoType) -> None:
        super().__init__("None", EikoObjectType)
        self.optional_type = optional_type

    def type_check(self, expected_type: "EikoType") -> bool:
        if expected_type is EikoNoneType:
            return True

        return expected_type.type_check(self.optional_type)

    def __repr__(self) -> str:
        return f"Optional[{self.optional_type}]"


class EikoNone(EikoBaseType):
    """Represents the None Value in the Eiko Language."""

    type = EikoNoneType

    def __init__(self, eiko_type: EikoType = EikoNoneType) -> None:
        super().__init__(eiko_type)
        self.value = None

    def get_value(self) -> None:
        return None

    def printable(self, _: str = "") -> str:
        return "None"

    def truthiness(self) -> bool:
        return False

    def index(self) -> str:
        return str(self.value)

    def to_py(self) -> None:
        return None


eiko_none_object = EikoNone()
EikoIntType = EikoType("int")


class EikoInt(EikoBaseType):
    """Represents an integer in the Eiko language."""

    type = EikoIntType

    def __init__(self, value: int, eiko_type: EikoType = EikoIntType) -> None:
        super().__init__(eiko_type)
        self.value = value

    def get_value(self) -> int:
        return self.value

    def printable(self, _: str = "") -> str:
        return f"{self.type} {self.value}"

    def truthiness(self) -> bool:
        return bool(self.value)

    def index(self) -> str:
        return str(self.value)

    @classmethod
    def convert(cls, obj: "BuiltinTypes") -> "EikoInt":
        """
        Converts the given value to an EikoInt.
        """
        value = obj.get_value()
        if isinstance(value, (str, int, float)):
            return cls(int(value))

        raise ValueError

    def to_py(self) -> int:
        return self.value


EikoFloatType = EikoType("float")


class EikoFloat(EikoBaseType):
    """Represents a float in the Eiko language."""

    type = EikoFloatType

    def __init__(self, value: float, eiko_type: EikoType = EikoFloatType) -> None:
        super().__init__(eiko_type)
        self.value = value

    def get_value(self) -> float:
        return self.value

    def printable(self, _: str = "") -> str:
        return f"{self.type} {self.value}"

    def truthiness(self) -> bool:
        return bool(self.value)

    def index(self) -> str:
        return str(self.value)

    @classmethod
    def convert(cls, obj: "BuiltinTypes") -> "EikoFloat":
        """
        Converts the given value to an EikoFloat.
        """
        value = obj.get_value()
        if isinstance(value, (str, int, float)):
            return cls(float(value))

        raise ValueError

    def to_py(self) -> float:
        return self.value


EikoNumber = Union[EikoInt, EikoFloat]

EikoBoolType = EikoType("bool")


class EikoBool(EikoBaseType):
    """Represents a boolean in the Eiko language."""

    type = EikoBoolType

    def __init__(self, value: bool, eiko_type: EikoType = EikoBoolType) -> None:
        super().__init__(eiko_type)
        self.value = value

    def get_value(self) -> bool:
        return self.value

    def printable(self, _: str = "") -> str:
        return f"{self.type} {self.value}"

    def truthiness(self) -> bool:
        return self.value

    def index(self) -> str:
        return str(self.value)

    @classmethod
    def convert(cls, obj: EikoBaseType) -> "EikoBool":
        return EikoBool(bool(obj.get_value()))

    def to_py(self) -> bool:
        return self.value


EikoStrType = EikoType("str")


class EikoStr(EikoBaseType):
    """Represents a string in the Eiko language."""

    type = EikoStrType

    def __init__(self, value: str, eiko_type: EikoType = EikoStrType) -> None:
        super().__init__(eiko_type)
        self.value = value

    def get_value(self) -> str:
        return self.value

    def printable(self, _: str = "") -> str:
        return f'{self.type} "{self.value}"'

    def truthiness(self) -> bool:
        return bool(self.value)

    def index(self) -> str:
        return self.value

    @classmethod
    def convert(cls, obj: "BuiltinTypes") -> "EikoStr":
        return cls(str(obj.get_value()))

    def to_py(self) -> str:
        return self.value


class EikoProtectedStr(EikoStr):
    """
    A protected string will not be printed to the cli,
    by std tools, nor can it be used for an index.
    """

    def printable(self, _: str = "") -> str:
        return "********"

    def index(self) -> str:
        raise EikoInternalError("A protrected string can not be used for an index.")


EikoPathType = EikoType("Path")


class EikoPath(EikoBaseType):
    """Represents a path in the Eiko language."""

    type = EikoPathType

    def __init__(self, value: Path, eiko_type: EikoType = EikoPathType) -> None:
        super().__init__(eiko_type)
        self.value = value

    def get_value(self) -> Path:
        return self.value

    def get(self, name: str, token: Optional[Token] = None) -> "EikoPath":
        if name == "parent":
            return EikoPath(self.value.parent)

        raise EikoCompilationError(
            f"Object of type '{self.type}' has no property '{name}'.",
            token=token,
        )

    def printable(self, _: str = "") -> str:
        return f'{self.type} "{self.value}"'

    def truthiness(self) -> bool:
        return bool(self.value)

    def index(self) -> str:
        return str(self.value)

    @classmethod
    def convert(cls, obj: "BuiltinTypes") -> "EikoPath":
        """
        Converts the given value to an EikoPath.
        """
        value = obj.get_value()
        if isinstance(value, str):
            return cls(Path(value))

        raise ValueError

    def to_py(self) -> Path:
        return self.value


T = TypeVar("T")


class EikoPromise(EikoBaseType, Generic[T]):
    """
    A promise is a piece of information that
    Eikobot might not be able to retrieve at compile time.
    Instead, this information will be filled in at deploy time.
    """

    def __init__(
        self,
        name: str,
        value_type: EikoType,
        caller_token: Token,
        parent: "EikoResource",
    ) -> None:
        super().__init__(value_type)
        self.name = name
        self.token = caller_token
        self.value: Optional[EikoBaseType] = None
        self.parent = parent

    def get(self, name: str, token: Optional[Token] = None) -> "EikoBaseType":
        raise EikoCompilationError(
            f"Object of type 'Promise' has no property '{name}'.",
            token=token,
        )

    def set(self, value: PyTypes, ctx: "HandlerContext") -> None:
        """
        Set this promise's value.
        This method will make sure the type is correct

        Raises ValueError if value is not the right type
        or if the promis was already assigned a different value.
        """
        _value = to_eiko(value)
        if not _value.type.type_check(self.type):
            raise ValueError

        if self.value is not None and _value.get_value() != self.value.get_value():
            ctx.error(
                f"Promise '{self.name}' already has a value and new value is different."
            )
            raise ValueError

        self.value = _value

    def assign(self, value: EikoBaseType, token: Optional[Token] = None) -> None:
        """
        Assign is used internally to assign a promise from inside the language,
        rather then from a handler.
        """
        if self.value is not None:
            raise EikoCompilationError(
                "Tried to assign an already assigned promise.",
                token=token,
            )

        if not value.type.type_check(self.type):
            raise EikoCompilationError(
                f"Tried to assign promise a value of type '{self.type.name}' "
                f"but got a value of type '{value.type.name}'.",
                token=token,
            )

        self.value = value

    def get_value(self) -> PyTypes:
        raise NotImplementedError

    def printable(self, _: str = "") -> str:
        return f"Promise[{self.type}]"

    def truthiness(self) -> bool:
        if self.value is None:
            raise EikoCompilationError(
                "An unfulfilled Promise cannot be checked for truthiness, "
                "as its value does not yet exist."
            )

        return self.value.truthiness()

    def index(self) -> str:
        return f"promise-{self.parent.index()}.{self.name}"

    def to_py(self) -> "EikoPromise[T]":
        return self

    def resolve(self, expect: Type[T]) -> T:
        """
        Gets the value of a promise if it exists.
        Raises EikoError if the promise has no value.
        The expect param allows for runtime type checking.
        """
        if self.value is None:
            raise EikoUnresolvedPromiseError(
                "Unresolved Promise was accessed.",
                token=self.token,
            )

        value = self.value.to_py()
        if isinstance(value, EikoPromise):
            value = value.resolve(expect)

        if not isinstance(value, expect):
            raise EikoError(
                f"Promise value is of type '{type(value)}', but user expected type '{expect}'."
            )

        return value


EikoEnumDefinitionType = EikoType("EnumDefinition")


class EikoEnumValue(EikoBaseType):
    """Represents values and instances of enum values"""

    def __init__(self, eiko_type: EikoType, value: str) -> None:
        super().__init__(eiko_type)
        self.value = value

    def index(self) -> str:
        return f"{self.type}-{self.value}"

    def printable(self, _: str = "") -> str:
        return f"{self.type.name} '{self.value}'"

    def get_value(self) -> str:
        return self.value

    def truthiness(self) -> bool:
        return True

    def to_py(self) -> str:
        return self.value


class EikoEnumDefinition(EikoBaseType):
    """Internal representation of a resource definition."""

    def __init__(
        self, name: str, value_type: EikoType, values: dict[str, EikoEnumValue]
    ) -> None:
        super().__init__(EikoEnumDefinitionType)
        self.name = name
        self.value_type = value_type
        self.values = values

    def get(self, name: str, token: Optional[Token] = None) -> EikoEnumValue:
        value = self.values.get(name)
        if value is None:
            raise EikoCompilationError(
                f"Enum '{self.name}' has no value '{name}'.",
                token=token,
            )

        return value

    def printable(self, indent: str = "") -> str:
        string = f"ENUM '{self.name}':" + " {\n"
        n_indent = indent + "    "
        for value in self.values.values():
            string += n_indent + value.printable(n_indent) + ",\n"
        string += indent + "}\n"

        return string

    @classmethod
    def convert(cls, _: "BuiltinTypes") -> "EikoBaseType":
        raise ValueError

    def get_value(self) -> PyTypes:
        raise NotImplementedError

    def truthiness(self) -> bool:
        raise NotImplementedError

    def index(self) -> str:
        raise NotImplementedError

    def to_py(self) -> Union[PyTypes, "EikoPromise"]:
        raise NotImplementedError


BuiltinTypes = Union[
    EikoBool, EikoFloat, EikoInt, EikoStr, EikoPath, EikoNone, EikoEnumValue
]
EikoBuiltinTypes = (
    EikoBool,
    EikoFloat,
    EikoInt,
    EikoStr,
    EikoPath,
    EikoNone,
    EikoEnumValue,
)


class EikoResource(EikoBaseType):
    """Represents a custom resource in the Eiko language."""

    def __init__(
        self,
        class_ref: "EikoResourceDefinition",
    ) -> None:
        super().__init__(class_ref.instance_type)
        self._index: str
        self.class_ref = class_ref
        self.properties: dict[str, Union[EikoBaseType, EikoUnset]] = {
            "__depends_on__": EikoList(EikoObjectType)
        }
        self.promises: dict[str, EikoPromise] = {}
        self._py_object: Optional["EikoBaseModel"] = None

    def set_index(self, index: str) -> None:
        self._index = index

    def get(self, name: str, token: Optional[Token] = None) -> EikoBaseType:
        value = self.properties.get(name)
        if value is None or isinstance(value, EikoUnset):
            raise EikoCompilationError(
                "Tried to access a property that does not exist.",
                token=token,
            )

        return value

    def get_value(self) -> dict[str, PyTypes]:
        return {key: value.get_value() for key, value in self.properties.items()}

    def get_external_promises(self) -> Iterator[tuple[str, EikoPromise]]:
        """Returns all promises that come from other resources."""
        for key, value in self.properties.items():
            if isinstance(value, EikoPromise):
                if value.name not in self.promises:
                    yield key, value

    def populate_property(self, name: str, value_type: EikoType) -> None:
        self.properties[name] = EikoUnset(value_type)

    def add_promise(self, promise: EikoPromise) -> None:
        self.properties[promise.name] = promise
        self.promises[promise.name] = promise

    def set(self, name: str, value: "StorableTypes", token: Token) -> None:
        """Set the value of a property, if the value wasn't already assigned."""
        if not isinstance(value, EikoBaseType):
            raise EikoCompilationError(
                f"Property '{name}' of class '{self.type}' "
                f"cannot be assigned a value of type '{value.type}'.",
                token=token,
            )

        prop = self.properties.get(name)
        if isinstance(prop, EikoUnset):
            if not value.type.type_check(prop.type):
                if prop.type.inverse_type_check(value.type):
                    if prop.type.typedef is not None:
                        value = prop.type.typedef.execute(value, token)
                    else:
                        raise EikoInternalError(
                            "Ran in to a typedef that does not have a constructor. "
                            "This is most likely a bug. PLease report this on Github.",
                            token=token,
                        )
                else:
                    raise EikoCompilationError(
                        f"Type error: Tried to assign value of type '{value.type}' "
                        f"to a property of type '{prop.type}'.",
                        token=token,
                    )

        elif isinstance(prop, EikoPromise):
            prop.assign(value, token)
            return

        elif prop is not None:
            raise EikoCompilationError(
                "Attempted to reassign a property that was already assigned.",
                token=token,
            )

        self.properties[name] = value

    def printable(self, indent: str = "") -> str:
        extra_indent = indent + "    "
        _repr = f"{self.type.name} '{self._index}': " + "{\n"
        for name, val in self.properties.items():
            if not (
                name == "__depends_on__"
                and isinstance(val, EikoList)
                and not val.elements
            ):
                _repr += extra_indent
                _repr += f"{val.type} '{name}': "
                _repr += val.printable(extra_indent)
                _repr += ",\n"

        _repr += indent + "}"

        return _repr

    def truthiness(self) -> bool:
        return True

    def index(self) -> str:
        return self._index

    def to_py(self) -> Union[BaseModel, dict]:
        if self._py_object is not None:
            return self._py_object

        new_dict: dict[str, Union[PyTypes, EikoPromise]] = {}
        pydantic_nested: dict[str, BaseModel] = {}
        for name, value in self.properties.items():
            if name in ["__depends_on__"]:
                continue
            new_value = value.to_py()
            if isinstance(new_value, EikoPromise):
                if new_value.name not in self.promises:
                    new_value = new_value.resolve(object)

            # Ok follow me on this:
            # Pydantic calls __dict__ when validating nested models
            # thereby returning new instances of objects that should not be recreated.
            # This can cause bugs as we rely on the objects staying the same.
            # So we keep track of all of the nested and attributes and
            # monkey patch them back in
            if isinstance(new_value, BaseModel) and isinstance(value, EikoResource):
                pydantic_nested[name] = new_value
            new_dict[name] = new_value

        if self.class_ref.linked_basemodel is not None:
            try:
                self._py_object = self.class_ref.linked_basemodel(
                    raw_resource=self, **new_dict
                )
                for name, pydantic_object in pydantic_nested.items():
                    object.__setattr__(self._py_object, name, pydantic_object)
                return self._py_object
            except ValidationError as e:
                raise EikoCompilationError(
                    f"Failed to convert resource of type '{self.class_ref.name}' to "
                    "its linked basemodel.\n"
                    f"Reason: {e}"
                ) from e

        return new_dict


INDEXABLE_TYPES = (
    EikoBool,
    EikoFloat,
    EikoInt,
    EikoNone,
    EikoStr,
    EikoPath,
    EikoPromise,
    EikoResource,
    EikoEnumValue,
)
_builtin_function_type = EikoType("builtin_function", EikoObjectType)


@dataclass
class PassedArg:
    """
    A passed arg is a compiled expression passed as an arg.
    This is an Arg meant to be passed to an EikoBuiltinFunction.
    """

    token: Token
    value: EikoBaseType


@dataclass
class BuiltinFunctionArg:
    """An arg passed to a builtin function."""

    name: str
    type: EikoType
    default_value: EikoBaseType | None = None


class EikoBuiltinFunction(EikoBaseType):
    """
    Built in functions are typically convenience functions.
    They cannot be user generated.
    """

    def __init__(
        self,
        identifier: str,
        args: list[BuiltinFunctionArg],
        body: Callable[..., Optional[EikoBaseType]],
    ) -> None:
        super().__init__(_builtin_function_type)
        self.identifier = identifier
        self.body = body

        self.args: list[BuiltinFunctionArg] = []
        self.kw_args: dict[str, BuiltinFunctionArg] = {}
        for arg in args:
            if arg.default_value is None:
                self.args.append(arg)
            else:
                self.kw_args[arg.name] = arg

    def execute(
        self,
        callee_token: Token,
        args: list[PassedArg],
        keyword_args: dict[str, PassedArg] | None = None,
    ) -> Optional[EikoBaseType]:
        """Execute the builtin function."""
        if len(args) > len(self.args) + len(self.kw_args):
            raise EikoCompilationError(
                "Too many arguments given to function call.",
                token=callee_token,
            )

        if len(args) < len(self.args):
            raise EikoCompilationError(
                "Missing positional arguments for function call.",
                token=callee_token,
            )

        validated_args: list[EikoBaseType] = []
        for passed_arg, expected_arg in zip(args, self.args):
            if not expected_arg.type.type_check(passed_arg.value.type):
                raise EikoCompilationError(
                    f"Argument '{expected_arg.name}' must be of type '{expected_arg.type}', "
                    f"but got '{passed_arg.value.type}' instead.",
                    token=passed_arg.token,
                )
            validated_args.append(passed_arg.value)

        validated_kw_args: dict[str, EikoBaseType] = {}
        if keyword_args is not None:
            for arg_name, passed_arg in keyword_args.items():
                expected_kw_arg = self.kw_args.get(arg_name)

                if expected_kw_arg is None:
                    raise EikoCompilationError(
                        f"Callable no such argument: '{arg_name}'.",
                        token=passed_arg.token,
                    )

                if not expected_kw_arg.type.type_check(passed_arg.value.type):
                    raise EikoCompilationError(
                        f"Argument '{expected_kw_arg.name}' must be of type '{expected_kw_arg.type}', "
                        f"but got '{passed_arg.value.type}' instead.",
                        token=passed_arg.token,
                    )

                validated_kw_args[arg_name] = passed_arg.value

        return self.body(*validated_args, **validated_kw_args)

    def truthiness(self) -> bool:
        raise NotImplementedError


class EikoListType(EikoType):
    """Represents an Eiko list type, which is a container of types."""

    def __init__(self, element_type: EikoType) -> None:
        super().__init__(f"list[{element_type.name}]")
        self.element_type = element_type

    def type_check(self, expected_type: "EikoType") -> bool:
        if isinstance(expected_type, EikoListType):
            return self.element_type.type_check(expected_type.element_type)

        return super().type_check(expected_type)


class EikoList(EikoBaseType):
    """Represents a list of objects in the Eiko language."""

    type: EikoListType

    def __init__(
        self,
        element_type: EikoType,
        elements: Optional[list[EikoBaseType]] = None,
    ) -> None:
        super().__init__(EikoListType(element_type))
        if elements is None:
            self.elements: list[EikoBaseType] = []
        else:
            self.elements = elements

        self.extend_func = EikoBuiltinFunction(
            "extend",
            [BuiltinFunctionArg("other", self.type)],
            body=self.extend,
        )
        self.append_func = EikoBuiltinFunction(
            "append",
            [BuiltinFunctionArg("element", element_type)],
            body=self.append,
        )

    def append(self, element: EikoBaseType) -> None:
        self.elements.append(element)

    def extend(self, other: "EikoList") -> None:
        self.elements.extend(other.elements)

    def update_typing(self, new_type: EikoListType) -> None:
        """Update the typing of a list after it was created."""
        self.type = new_type
        self.extend_func = EikoBuiltinFunction(
            "extend",
            [BuiltinFunctionArg("other", new_type)],
            body=self.extend,
        )
        self.append_func = EikoBuiltinFunction(
            "append",
            [BuiltinFunctionArg("element", new_type.element_type)],
            body=self.append,
        )

    def get(self, name: str, token: Optional[Token] = None) -> "EikoBaseType":
        if name == "append":
            return self.append_func

        if name == "extend":
            return self.extend_func

        return super().get(name, token)

    def get_index(self, index: int) -> Optional[EikoBaseType]:
        """Gets an element by its index, if it exists."""
        try:
            return self.elements[index]
        except IndexError:
            return None

    def get_value(self) -> list[PyTypes]:
        return [value.get_value() for value in self.elements]

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

    def index(self) -> str:
        raise NotImplementedError

    def to_py(self) -> list[Union[PyTypes, "EikoPromise"]]:
        return [element.to_py() for element in self.elements]

    def iterate(self, _: Token) -> Iterator["EikoBaseType"]:
        for element in self.elements:
            yield element


class EikoDictType(EikoType):
    """Represents an Eiko Union type, which combines 2 or more types."""

    def __init__(self, key_type: EikoType, value_type: EikoType) -> None:
        super().__init__(f"dict[{key_type.name}, {value_type.name}]")
        self.key_type = key_type
        self.value_type = value_type

    def type_check(self, expected_type: "EikoType") -> bool:
        if isinstance(expected_type, EikoDictType):
            if self.key_type.type_check(
                expected_type.key_type
            ) and self.value_type.type_check(expected_type.value_type):
                return True

        return super().type_check(expected_type)


EikoIndexTypes = Union[
    bool,
    float,
    int,
    None,
    str,
]


class EikoDict(EikoBaseType):
    """Represents a list of objects in the Eiko language."""

    type: EikoDictType

    def __init__(
        self,
        key_type: EikoType,
        value_type: EikoType,
        elements: Optional[
            dict[Union[EikoBaseType, bool, float, int, str], EikoBaseType]
        ] = None,
    ) -> None:
        super().__init__(EikoDictType(key_type, value_type))
        self.elements: dict[Union[EikoBaseType, bool, float, int, str], EikoBaseType]
        if elements is None:
            self.elements = {}
        else:
            self.elements = elements

        self.get_func = EikoBuiltinFunction(
            "get",
            [
                BuiltinFunctionArg("key", key_type),
                BuiltinFunctionArg("default_value", eiko_any_type, eiko_none_object),
            ],
            body=self._get,
        )

        self.values_func = EikoBuiltinFunction(
            "values",
            [],
            body=self._values,
        )

    def _get(
        self,
        key: Union[EikoBaseType, bool, float, int, str],
        default_value: EikoBaseType = eiko_none_object,
    ) -> EikoBaseType:
        return self.elements.get(key, default_value)

    def _values(self) -> EikoList:
        return EikoList(self.type.value_type, list(self.elements.values()))

    def update_typing(self, new_type: EikoDictType) -> None:
        self.type = new_type

    def insert(
        self,
        key: EikoBaseType,
        value: EikoBaseType,
        key_token: Optional[Token] = None,
        value_token: Optional[Token] = None,
    ) -> bool:
        """Insert an element in to the dictionary"""
        if not self.type.key_type.type_check(key.type):
            raise EikoCompilationError(
                f"Expected key of type '{self.type.key_type}', but was given type {key.type}",
                token=key_token,
            )

        if not self.type.value_type.type_check(value.type):
            raise EikoCompilationError(
                f"Expected key of type '{self.type.value_type}', but was given type {value.type}",
                token=value_token,
            )

        _key: Union[EikoBaseType, bool, float, int, str]

        if isinstance(key, (EikoBool, EikoFloat, EikoInt, EikoStr)):
            _key = key.value
        else:
            _key = key

        prev_value = self.elements.get(_key)
        if prev_value is not None:
            return False

        self.elements[_key] = value
        return True

    def get_value(self) -> dict[EikoIndexTypes, PyTypes]:
        n_dict: dict[EikoIndexTypes, PyTypes] = {}
        n_key: EikoIndexTypes
        for key, value in self.elements.items():
            if isinstance(key, EikoResource):
                n_key = key.index()
            elif isinstance(key, (bool, float, int, str)) or key is None:
                n_key = key
            elif isinstance(key, (EikoBool, EikoFloat, EikoInt, EikoNone, EikoStr)):
                n_key = key.get_value()
            else:
                raise EikoInternalError(
                    "A non indexable type was passed to a dictionary, "
                    "but this should have been caught earlier in the compilation process. "
                    "Please report this bug."
                )

            n_dict[n_key] = value.get_value()

        return n_dict

    def get_index(
        self,
        key: EikoBaseType,
        key_token: Optional[Token] = None,
    ) -> EikoBaseType:
        """Get a value based on it's index."""
        if not self.type.key_type.type_check(key.type):
            raise EikoCompilationError(
                f"Expected key of type '{self.type.key_type}', but got '{key.type}'.",
                token=key_token,
            )

        _key: Union[EikoBaseType, bool, float, int, str]
        if isinstance(key, (EikoBool, EikoFloat, EikoInt, EikoStr)):
            _key = key.value
        else:
            _key = key

        value = self.elements.get(_key)

        if value is None:
            raise EikoCompilationError(
                "No value stored for given key.",
                token=key_token,
            )

        return value

    def printable(self, indent: str = "") -> str:
        extra_indent = indent + "    "
        _repr = "{\n"
        for key, val in self.elements.items():
            _repr += extra_indent
            if not isinstance(key, EikoBaseType):
                key = to_eiko(key)

            _repr += key.printable(extra_indent) + ": "
            _repr += val.printable(extra_indent) + ",\n"

        _repr += indent + "}"
        return _repr

    def truthiness(self) -> bool:
        return bool(self.elements)

    def index(self) -> str:
        raise NotImplementedError

    def to_py(
        self,
    ) -> dict[Union[PyTypes, "EikoPromise"], Union[PyTypes, "EikoPromise"]]:
        py_dict: dict[Union[PyTypes, "EikoPromise"], Union[PyTypes, "EikoPromise"]] = {}
        for key, value in self.elements.items():
            _key: Union[PyTypes, "EikoPromise"]
            if isinstance(key, EikoBaseType):
                _key = key.to_py()
            else:
                _key = key

            py_dict[_key] = value.to_py()

        return py_dict

    @staticmethod
    def convert_key(
        key: EikoBaseType, key_token: Optional[Token] = None
    ) -> Union[EikoBaseType, bool, float, int, str]:
        """Converts a given value to one that can be used as a key."""
        if isinstance(key, (EikoBool, EikoFloat, EikoInt, EikoStr)):
            return key.value

        if isinstance(key, (EikoNone, EikoResource)):
            return key

        raise EikoCompilationError(
            f"Object of type '{key.type.name}' can not be for keys in dictionairies.",
            token=key_token,
        )

    def iterate(self, _: Token) -> Iterator["EikoBaseType"]:
        for element in self.elements:
            yield to_eiko(element)

    def get(self, name: str, token: Optional[Token] = None) -> "EikoBaseType":
        if name == "values":
            return self.values_func

        if name == "get":
            return self.get_func

        return super().get(name, token)


# Move to another file
def to_eiko_type(cls: Optional[Type]) -> Type[EikoBaseType] | Type[EikoType]:
    """
    Takes a python type and returns it's eikobot compatible type.
    If said type exists.
    """
    if cls is None:
        return EikoNone

    if issubclass(cls, EikoBaseType) or issubclass(cls, EikoType):
        return cls

    if cls == bool:
        return EikoBool

    if cls == float:
        return EikoFloat

    if cls == int:
        return EikoInt

    if cls == str:
        return EikoStr

    if cls == Path:
        return EikoPath

    if hasattr(cls, "__origin__"):
        if cls.__origin__ == list:
            return EikoList

        if cls.__origin__ == dict:
            return EikoDict

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

    if isinstance(value, Path):
        return EikoPath(value)

    if isinstance(value, list):
        elements: list[EikoBaseType] = []
        types: list[EikoType] = []
        for x in value:
            element = to_eiko(x)
            elements.append(element)
            types.append(element.type)

        return EikoList(type_list_to_type(types), elements)

    if isinstance(value, dict):
        d_elements: dict[Union[EikoBaseType, bool, float, int, str], EikoBaseType] = {}
        key_types: list[EikoType] = []
        value_types: list[EikoType] = []
        for _key, _value in value.items():
            eiko_key = to_eiko(_key)
            key_types.append(eiko_key.type)
            eiko_value = to_eiko(_value)
            value_types.append(eiko_value.type)
            d_elements[EikoDict.convert_key(eiko_key)] = eiko_value

        return EikoDict(
            type_list_to_type(key_types), type_list_to_type(value_types), d_elements
        )

    if isinstance(value, EikoBaseType):
        return value

    if isinstance(value, BaseModel) and hasattr(value, "raw_resource"):
        return value.raw_resource  # type: ignore

    if value is None:
        return eiko_none_object

    raise ValueError
