from dataclasses import dataclass
from typing import List, Union

from .compilation_context import ResourceDefinition, ResourceProperty
from .eiko_types import EikoBaseType, EikoBool, EikoFloat, EikoInt, EikoStr
from .errors import EikoCompilationError, EikoInternalError
from .ops import BINOP_MATRIX, BinOP
from .token import Token, TokenType


@dataclass
class ExprAST:
    """Base ExprAST. Purely Virtual."""

    token: Token

    def compile(self) -> EikoBaseType:
        raise NotImplementedError


@dataclass
class EOFExprAST(ExprAST):  # pylint: disable=abstract-method
    """This ExprAST marks end of parsing."""


@dataclass
class IntExprAST(ExprAST):
    """AST representing an integer in the source"""

    def __post_init__(self) -> None:
        self.value = int(self.token.content)

    def compile(self) -> EikoInt:
        return EikoInt(self.value)


@dataclass
class FloatExprAST(ExprAST):
    """AST representing a float in the source."""

    def __post_init__(self) -> None:
        self.value = float(self.token.content)

    def compile(self) -> EikoFloat:
        return EikoFloat(self.value)


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

    def compile(self) -> EikoBool:
        return EikoBool(self.value)


@dataclass
class StringExprAST(ExprAST):
    """AST representing a string in the source."""

    def __post_init__(self) -> None:
        self.value = self.token.content

    def compile(self) -> EikoStr:
        return EikoStr(self.value)


@dataclass
class UnaryNotExprAST(ExprAST):
    """AST representing a unary not operation."""

    rhs: ExprAST


@dataclass
class UnaryNegExprAST(ExprAST):
    """AST representing a unary negative operation."""

    rhs: ExprAST

    def compile(self) -> Union[EikoInt, EikoFloat]:
        rhs = self.rhs.compile()
        if isinstance(rhs, EikoInt):
            return EikoInt(-rhs.value)

        if isinstance(rhs, EikoFloat):
            return EikoFloat(-rhs.value)

        raise EikoCompilationError(
            f"Unable to perform unary negative on object of type {rhs.type}",
            token=self.token,
        )


@dataclass
class BinOpExprAST(ExprAST):
    """A binary operation taking a left and right hand side."""

    lhs: ExprAST
    rhs: ExprAST

    def __post_init__(self) -> None:
        self.bin_op = BinOP.from_str(self.token.content)

    def compile(self) -> EikoBaseType:
        lhs = self.lhs.compile()
        rhs = self.rhs.compile()

        arg_a_matrix = BINOP_MATRIX.get(lhs.type)
        if arg_a_matrix is None:
            raise EikoCompilationError(
                f"No overload of operation {self.bin_op} for arguments"
                f"of types {lhs.type} and {rhs.type} available.",
                token=self.token,
            )

        arg_b_matrix = arg_a_matrix.get(rhs.type)
        if arg_b_matrix is None:
            raise EikoCompilationError(
                f"No overload of operation {self.bin_op} for arguments"
                f"of types {lhs.type} and {rhs.type} available.",
                token=self.token,
            )

        op = arg_b_matrix.get(self.bin_op)
        if op is None:
            raise EikoCompilationError(
                f"No overload of operation {self.bin_op} for arguments"
                f"of types {lhs.type} and {rhs.type} available.",
                token=self.token,
            )

        return op(lhs, rhs)  # type: ignore


@dataclass
class ResourceDefinitionAST(ExprAST):
    name: str

    def __post_init__(self) -> None:
        self.properties: List[ResourceProperty] = []

    def add_property(self, new_property: ResourceProperty, token: Token) -> None:
        for existing_property in self.properties:
            if new_property.name == existing_property.name:
                raise EikoCompilationError(
                    f"Redefining property {new_property.name} "
                    f"for Resource type {self.name}, ",
                    "this is not allowed.",
                    token=token,
                )

        self.properties.append(new_property)

    def compile(self) -> ResourceDefinition:
        return ResourceDefinition(self.name, self.properties)
