from dataclasses import dataclass
from enum import Enum, auto

from .errors import EikoInternalError
from .token import Token, TokenType


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


@dataclass
class ExprAST:
    """Base ExprAST. Purely Virtual."""

    token: Token


@dataclass
class EOFExprAST(ExprAST):
    """This ExprAST marks end of parsing."""


@dataclass
class IntExprAST(ExprAST):
    """AST representing an integer in the source"""

    def __post_init__(self) -> None:
        self.value = int(self.token.content)


@dataclass
class FloatExprAST(ExprAST):
    """AST representing a float in the source."""

    def __post_init__(self) -> None:
        self.value = float(self.token.content)


@dataclass
class BoolExprAST(ExprAST):
    """AST representing a bool in the source."""

    def __post_init__(self) -> None:
        if self.token.type == TokenType.FALSE:
            self.value = False
        elif self.token.type == TokenType.TRUE:
            self.value = True
        else:
            raise EikoInternalError(
                "Error occured trying to compile BoolExprAST. "
                "This is deffinetly a bug, please report it on github."
            )


@dataclass
class StringExprAST(ExprAST):
    """AST representing a string in the source."""

    def __post_init__(self) -> None:
        self.value = self.token.content


@dataclass
class UnaryNotExprAST(ExprAST):
    """AST representing a unary not operation."""

    rhs: ExprAST


@dataclass
class UnaryNegExprAST(ExprAST):
    """AST representing a unary negative operation."""

    rhs: ExprAST


@dataclass
class BinOpExprAST(ExprAST):
    """A binary operation taking a left and right hand side."""

    lhs: ExprAST
    rhs: ExprAST

    def __post_init__(self) -> None:
        self.bin_op = BinOP.from_str(self.token.content)
