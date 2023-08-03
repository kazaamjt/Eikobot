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
    AND = auto()
    OR = auto()
    DEF = auto()
    PROMISE = auto()
    ENUM = auto()
    FOR = auto()
    IN = auto()

    IDENTIFIER = auto()

    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_SQ_BRACKET = auto()
    RIGHT_SQ_BRACKET = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    COLON = auto()
    COMMA = auto()
    DOT = auto()
    DOUBLE_DOT = auto()
    TRIPLE_DOT = auto()
    AT_SIGN = auto()

    DOUBLE_COLON = auto()
    ASSIGNMENT_OP = auto()
    ARITHMETIC_OP = auto()
    COMPARISON_OP = auto()

    # Base types
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    F_STRING = auto()
    TRUE = auto()
    FALSE = auto()

    INDENT = auto()
    EOF = auto()
    UNKNOWN = auto()


token_to_char = {
    TokenType.LEFT_PAREN: "(",
    TokenType.RIGHT_PAREN: ")",
    TokenType.LEFT_SQ_BRACKET: "[",
    TokenType.RIGHT_SQ_BRACKET: "]",
    TokenType.LEFT_BRACE: "{",
    TokenType.RIGHT_BRACE: "}",
    TokenType.COMMA: ",",
    TokenType.DOT: ".",
    TokenType.AT_SIGN: "@",
}


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
