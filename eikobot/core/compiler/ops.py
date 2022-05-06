"""
Eikobot binary operations,
allowing the addition, multiplication, division, etc...
of Eikobot builtin types.
"""
from enum import Enum, auto
from typing import Callable, Dict, Union

from .definitions.base_types import (
    EikoBaseType,
    EikoFloat,
    EikoInt,
    EikoNumber,
    EikoStr,
)
from .errors import EikoInternalError


class BinOP(Enum):
    """Eiko supported binary operations"""

    ADD = auto()
    SUBTRACT = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    INT_DIVIDE = auto()
    EXPONENTIATION = auto()

    @staticmethod
    def from_str(op: str) -> "BinOP":
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

        raise EikoInternalError(
            "Issue occured trying to parse binop. "
            "This is deffinetly a bug, please report it on github.",
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
    return EikoInt(a.value ** b.value)


def add_float(a: EikoNumber, b: EikoNumber) -> EikoFloat:
    return EikoFloat(a.value + b.value)


def subtract_float(a: EikoNumber, b: EikoNumber) -> EikoFloat:
    return EikoFloat(a.value - b.value)


def multiply_float(a: EikoNumber, b: EikoNumber) -> EikoFloat:
    return EikoFloat(a.value * b.value)


def divide_float(a: EikoNumber, b: EikoNumber) -> EikoFloat:
    return EikoFloat(a.value / b.value)


def exponentiate_float(a: EikoNumber, b: EikoNumber) -> EikoFloat:
    return EikoFloat(a.value ** b.value)


def add_string(a: EikoStr, b: EikoStr) -> EikoStr:
    return EikoStr(a.value + b.value)


def multiply_string(a: EikoStr, b: EikoInt) -> EikoStr:
    return EikoStr(a.value * b.value)


BinOpCallable = Union[
    Callable[[EikoInt, EikoInt], EikoBaseType],
    Callable[[EikoStr, EikoInt], EikoBaseType],
    Callable[[EikoStr, EikoStr], EikoBaseType],
    Callable[[EikoNumber, EikoNumber], EikoBaseType],
    Callable[[EikoBaseType, EikoBaseType], EikoBaseType],
]

BinOpMatrix = Dict[BinOP, BinOpCallable]

_float_matrix: BinOpMatrix = {
    BinOP.ADD: add_float,
    BinOP.SUBTRACT: subtract_float,
    BinOP.MULTIPLY: multiply_float,
    BinOP.DIVIDE: divide_float,
    BinOP.INT_DIVIDE: divide_float,
    BinOP.EXPONENTIATION: exponentiate_float,
}

BINOP_MATRIX: Dict[str, Dict[str, BinOpMatrix]] = {
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
}
