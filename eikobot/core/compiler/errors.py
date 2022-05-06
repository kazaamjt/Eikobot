"""
Error types raised by the Eikobot compiler.
"""
from typing import Optional

from .misc import Index
from .token import Token


class EikoError(Exception):
    """An error that occured during the eiko compilation process."""

    def __init__(self, *args: object, token: Optional[Token] = None) -> None:
        super().__init__(*args)
        self.token = token
        self.index = None if token is None else token.index


class EikoInternalError(EikoError):
    """
    Something went wrong inside the compiler,
    most likely caused by a bug and not the user.
    """


class EikoSyntaxError(EikoError):
    """
    A syntax error that either confused the parser or the lexer.
    """

    def __init__(self, *args: object, index: Optional[Index] = None) -> None:
        super().__init__(*args)
        self.index = index


class EikoParserError(EikoError):
    """
    An error that occured while parsing.
    Usually an unexpected token or similar.
    """


class EikoCompilationError(EikoError):
    """
    An error that occured during the compilation step.
    """
