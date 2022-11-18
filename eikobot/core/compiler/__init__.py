"""
The entrypoint of the Eikobot Compiler.
The compiler takes output from lexers/parsers
and uses the resulting asts to create a model.
"""
from pathlib import Path

from .definitions.base_types import EikoResource
from .definitions.context import CompilerContext
from .importlib import import_python_code
from .parser import AssignmentExprAST, Parser


class Compiler:
    """
    The compiler takes output from lexers/parsers and uses
    the resulting asts to create a model.
    """

    def __init__(self) -> None:
        self.context = CompilerContext("__main__")

    def compile(self, file: Path) -> None:
        """Compiles an Eikobot file given a path."""
        self.context.set_path(file)
        import_python_code(["__main__"], file, self.context)

        for expr in Parser(file).parse():
            result = expr.compile(self.context)
            if isinstance(result, EikoResource) and not isinstance(
                expr, AssignmentExprAST
            ):
                self.context.orphans.append(result)

    def reset(self) -> None:
        """Resets the compiler context for reuse."""
        self.context = CompilerContext("__main__")
