from typing import Optional

from .token import Token


class EikoError(Exception):
    """An error that occured during the eiko compilation process."""

    def __init__(self, *args: object, token: Optional[Token] = None) -> None:
        super().__init__(*args)
        self.token = token


class EikoInternalError(EikoError):
    """
    Something went wrong inside the compiler,
    most likely caused by a bug and not the user.
    """


class EikoSyntaxError(EikoError):
    """
    A syntax error that either confused the parser or the lexer.
    """


class EikoParserError(EikoError):
    """
    An error that occured while parsing.
    Usually an unexpected token or similar.
    """


class EikoCompilationError(EikoError):
    """
    An error that occured during the compilation step.
    """
