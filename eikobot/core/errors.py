"""
Error types raised by the Eikobot compiler.
"""
from typing import Optional

from .compiler._token import Token
from .compiler.misc import Index


class EikoError(Exception):
    """An error that occured during the eiko compilation process."""

    def __init__(
        self, reason: str, *args: object, token: Optional[Token] = None
    ) -> None:
        super().__init__(reason, *args)
        self.token = token
        self.index = None if token is None else token.index


class EikoUnresolvedPromiseError(EikoError):
    """A promise that wasn't resolved by the time it was accessed"""


class EikoInternalError(EikoError):
    """
    Something went wrong inside the compiler,
    most likely caused by a bug and not the user.
    """

    def __init__(
        self, reason: str, *args: object, token: Optional[Token] = None
    ) -> None:
        super().__init__("PANIC!! " + reason, *args, token=token)


class EikoSyntaxError(EikoError):
    """
    A syntax error that either confused the parser or the lexer.
    """

    def __init__(
        self, reason: str, *args: object, index: Optional[Index] = None
    ) -> None:
        super().__init__("SyntaxError: " + reason, *args)
        self.index = index


class EikoParserError(EikoError):
    """
    An error that occured while parsing.
    Usually an unexpected token or similar.
    """

    def __init__(
        self, reason: str, *args: object, token: Optional[Token] = None
    ) -> None:
        super().__init__("SyntaxError: " + reason, *args, token=token)


class EikoCompilationError(EikoError):
    """
    An error that occured during the compilation step.
    """

    def __init__(
        self, reason: str, *args: object, token: Optional[Token] = None
    ) -> None:
        super().__init__("CompilationError: " + reason, *args, token=token)


class EikoPluginError(EikoError):
    """
    An error that happened while calling a plugin.
    """

    def __init__(
        self,
        reason: str,
        *args: object,
        token: Optional[Token] = None,
        python_exception: Optional[Exception] = None,
    ) -> None:
        super().__init__("PluginError: " + reason, *args, token=token)
        self.python_exception = python_exception


class EikoExportError(EikoError):
    """
    Something went wrong inside the compiler,
    most likely caused by a bug and not the user.
    """

    def __init__(
        self, reason: str, *args: object, token: Optional[Token] = None
    ) -> None:
        super().__init__("ExportError: " + reason, *args, token=token)


class EikoDeployError(EikoError):
    """
    Something went wrong inside the compiler,
    most likely caused by a bug and not the user.
    """

    def __init__(
        self, reason: str, *args: object, token: Optional[Token] = None
    ) -> None:
        super().__init__("DeployError: " + reason, *args, token=token)
