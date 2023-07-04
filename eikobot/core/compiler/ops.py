"""
Eikobot binary operations,
allowing the addition, multiplication, division, etc...
of Eikobot builtin types.
"""
from enum import Enum, auto
from pathlib import Path
from typing import Callable, Union

from ..errors import EikoCompilationError, EikoInternalError, EikoSyntaxError
from .definitions.base_types import (
    EikoBaseType,
    EikoBool,
    EikoFloat,
    EikoInt,
    EikoNumber,
    EikoPath,
    EikoResource,
    EikoStr,
    EikoUnset,
)
from .lexer import Token


class BinOP(Enum):
    """Eiko supported binary operations"""

    ADD = auto()
    SUBTRACT = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    INT_DIVIDE = auto()
    EXPONENTIATION = auto()

    @staticmethod
    def from_str(op: str, token: Token) -> "BinOP":
        """Turns a string in to a bin_op"""
        if op == "+":
            return BinOP.ADD

        if op == "-":
            return BinOP.SUBTRACT

        if op == "*":
            return BinOP.MULTIPLY

        if op == "/":
            return BinOP.DIVIDE

        if op == "//":
            return BinOP.INT_DIVIDE

        if op == "**":
            return BinOP.EXPONENTIATION

        raise EikoSyntaxError(
            "Issue occured trying to parse binop.",
            index=token.index,
        )

    def __str__(self) -> str:
        if self == BinOP.ADD:
            return "+"
        if self == BinOP.SUBTRACT:
            return "-"
        if self == BinOP.MULTIPLY:
            return "*"
        if self == BinOP.DIVIDE:
            return "/"
        if self == BinOP.INT_DIVIDE:
            return "//"
        if self == BinOP.EXPONENTIATION:
            return "**"

        raise EikoInternalError(
            "This is a bug. Somehow this happned. "
            "It shouldn't be possible for this bug to happen, yet here we are."
        )


def add_int(a: EikoInt, b: EikoInt) -> EikoInt:
    return EikoInt(a.value + b.value)


def subtract_int(a: EikoInt, b: EikoInt) -> EikoInt:
    return EikoInt(a.value - b.value)


def multiply_int(a: EikoInt, b: EikoInt) -> EikoInt:
    return EikoInt(a.value * b.value)


def divide_int(a: EikoInt, b: EikoInt) -> EikoInt:
    return EikoInt(a.value // b.value)


def exponentiate_int(a: EikoInt, b: EikoInt) -> EikoInt:
    return EikoInt(a.value**b.value)


def add_float(a: EikoNumber, b: EikoNumber) -> EikoFloat:
    return EikoFloat(a.value + b.value)


def subtract_float(a: EikoNumber, b: EikoNumber) -> EikoFloat:
    return EikoFloat(a.value - b.value)


def multiply_float(a: EikoNumber, b: EikoNumber) -> EikoFloat:
    return EikoFloat(a.value * b.value)


def divide_float(a: EikoNumber, b: EikoNumber) -> EikoFloat:
    return EikoFloat(a.value / b.value)


def exponentiate_float(a: EikoNumber, b: EikoNumber) -> EikoFloat:
    return EikoFloat(a.value**b.value)


def add_string(a: EikoStr, b: EikoStr) -> EikoStr:
    return EikoStr(a.value + b.value)


def multiply_string(a: EikoStr, b: EikoInt) -> EikoStr:
    return EikoStr(a.value * b.value)


def divide_path(a: EikoPath, b: Union[EikoPath, EikoStr]) -> EikoPath:
    return EikoPath(Path(a.value / b.value))


BinOpCallable = Union[
    Callable[[EikoInt, EikoInt], EikoBaseType],
    Callable[[EikoStr, EikoInt], EikoBaseType],
    Callable[[EikoStr, EikoStr], EikoBaseType],
    Callable[[EikoNumber, EikoNumber], EikoBaseType],
    Callable[[EikoBaseType, EikoBaseType], EikoBaseType],
    Callable[[EikoPath, Union[EikoPath, EikoStr]], EikoBaseType],
]

BinOpMatrix = dict[BinOP, BinOpCallable]

_float_matrix: BinOpMatrix = {
    BinOP.ADD: add_float,
    BinOP.SUBTRACT: subtract_float,
    BinOP.MULTIPLY: multiply_float,
    BinOP.DIVIDE: divide_float,
    BinOP.INT_DIVIDE: divide_float,
    BinOP.EXPONENTIATION: exponentiate_float,
}

BINOP_MATRIX: dict[str, dict[str, BinOpMatrix]] = {
    "int": {
        "int": {
            BinOP.ADD: add_int,
            BinOP.SUBTRACT: subtract_int,
            BinOP.MULTIPLY: multiply_int,
            BinOP.DIVIDE: divide_float,
            BinOP.INT_DIVIDE: divide_int,
            BinOP.EXPONENTIATION: exponentiate_int,
        },
        "float": _float_matrix.copy(),
    },
    "float": {"int": _float_matrix.copy(), "float": _float_matrix.copy()},
    "str": {
        "int": {
            BinOP.MULTIPLY: multiply_string,
        },
        "str": {
            BinOP.ADD: add_string,
        },
    },
    "Path": {
        "str": {
            BinOP.DIVIDE: divide_path,
        },
        "path": {
            BinOP.DIVIDE: divide_path,
        },
    },
}


class ComparisonOP(Enum):
    """Eiko supported binary operations"""

    LESS_THEN = auto()
    GREATHER_THEN = auto()
    EQUALS = auto()
    EQ_OR_GT = auto()
    EQ_OR_LT = auto()

    @staticmethod
    def from_str(token: Token) -> "ComparisonOP":
        """Turns a string in to a bin_op"""
        if token.content == "<":
            return ComparisonOP.LESS_THEN

        if token.content == ">":
            return ComparisonOP.GREATHER_THEN

        if token.content == "==":
            return ComparisonOP.EQUALS

        if token.content == ">=":
            return ComparisonOP.EQ_OR_GT

        if token.content == "<=":
            return ComparisonOP.EQ_OR_LT

        raise EikoSyntaxError(
            "Issue occured trying to parse binop.",
            index=token.index,
        )

    def __str__(self) -> str:
        if self == ComparisonOP.LESS_THEN:
            return "<"

        if self == ComparisonOP.GREATHER_THEN:
            return ">"

        if self == ComparisonOP.EQUALS:
            return "=="

        if self == ComparisonOP.EQ_OR_GT:
            return ">="

        if self == ComparisonOP.EQ_OR_LT:
            return "<="

        raise EikoInternalError(
            "Ran in to a bug. Somehow this happened. "
            "It shouldn't be possible for this bug to happen, yet here we are."
        )


def _number_compare(a: EikoNumber, b: EikoNumber, op: ComparisonOP) -> EikoBool:
    if op == ComparisonOP.EQ_OR_GT:
        return EikoBool(a.value >= b.value)

    if op == ComparisonOP.EQ_OR_LT:
        return EikoBool(a.value <= b.value)

    if op == ComparisonOP.GREATHER_THEN:
        return EikoBool(a.value > b.value)

    if op == ComparisonOP.LESS_THEN:
        return EikoBool(a.value < b.value)

    raise EikoInternalError(
        "Ran in to a bug. Somehow this happened. "
        "It shouldn't be possible for this bug to happen, yet here we are."
    )


def _str_compare(a: EikoStr, b: EikoStr, op: ComparisonOP) -> EikoBool:
    if op == ComparisonOP.EQ_OR_GT:
        return EikoBool(a.value >= b.value)

    if op == ComparisonOP.EQ_OR_LT:
        return EikoBool(a.value <= b.value)

    if op == ComparisonOP.GREATHER_THEN:
        return EikoBool(a.value > b.value)

    if op == ComparisonOP.LESS_THEN:
        return EikoBool(a.value < b.value)

    raise EikoInternalError(
        "Ran in to a bug. Somehow this happened. "
        "It shouldn't be possible for this bug to happen, yet here we are."
    )


def _eq_compare(
    a: EikoBaseType, b: EikoBaseType, op: ComparisonOP, b_token: Token
) -> EikoBool:
    if a is b:
        return EikoBool(True)

    if isinstance(a, (EikoInt, EikoFloat)) and isinstance(b, (EikoInt, EikoFloat)):
        return EikoBool(a.value == b.value)

    if not a.type == b.type:
        return EikoBool(False)

    if isinstance(a, EikoStr) and isinstance(b, EikoStr):
        return EikoBool(a.value == b.value)

    if isinstance(a, EikoBool) and isinstance(b, EikoBool):
        return EikoBool(a.value == b.value)

    if isinstance(a, EikoResource) and isinstance(b, EikoResource):
        for name, prop_a in a.properties.items():
            prop_b = b.properties.get(name)
            if prop_b is None:
                return EikoBool(False)

            if isinstance(prop_a, EikoUnset) or isinstance(prop_b, EikoUnset):
                if not (
                    isinstance(prop_a, EikoUnset) and isinstance(prop_b, EikoUnset)
                ):
                    return EikoBool(False)

            elif not compare(prop_a, prop_b, op, b_token):
                return EikoBool(False)

        return EikoBool(True)

    return EikoBool(False)


def compare(
    a: EikoBaseType, b: EikoBaseType, op: ComparisonOP, b_token: Token
) -> EikoBool:
    "Given 2 eiko objects and a comparison operator, performs a comparison."
    if op == ComparisonOP.EQUALS:
        return _eq_compare(a, b, op, b_token)

    if isinstance(a, (EikoInt, EikoFloat)) and isinstance(b, (EikoInt, EikoFloat)):
        return _number_compare(a, b, op)

    if isinstance(a, EikoStr) and isinstance(b, EikoStr):
        return _str_compare(a, b, op)

    raise EikoCompilationError(
        f"Cannot perform operation '{op}' for '{a.type}' and '{b.type}'.",
        token=b_token,
    )
