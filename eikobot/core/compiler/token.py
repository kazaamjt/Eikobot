"""
Lexer Tokens describe source content.
They are used to construct the AST by the parser.
"""
from dataclasses import dataclass
from enum import Enum, auto

from .misc import Index


class TokenType(Enum):
    """
    Enum of all potential TokenTypes.
    """

    RESOURCE = auto()
    IMPLEMENT = auto()
    FROM = auto()
    IMPORT = auto()
    TYPEDEF = auto()
    IF = auto()
    ELIF = auto()
    ELSE = auto()

    IDENTIFIER = auto()
    F_STRING = auto()

    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    COLON = auto()
    COMMA = auto()
    DOT = auto()
    AT_SIGN = auto()

    DOUBLE_COLON = auto()
    ASSIGNMENT_OP = auto()
    ARITHMETIC_OP = auto()
    COMPARISON_OP = auto()

    # Base types
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    TRUE = auto()
    FALSE = auto()

    INDENT = auto()
    EOF = auto()
    UNKNOWN = auto()


@dataclass
class Token:
    """
    A token represents a gramatical construct
    that can be used to build the AST.
    """

    type: TokenType
    content: str
    index: Index

    def __repr__(self) -> str:
        return f"Token(type=<{self.type.name}>, index=<{self.index.__repr__()}>)"
