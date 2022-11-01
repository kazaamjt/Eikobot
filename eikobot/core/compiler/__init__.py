"""
The entrypoint of the Eikobot Compiler.
The compiler takes output from lexers/parsers
and uses the resulting asts to create a model.
"""
from pathlib import Path

from .definitions.context import CompilerContext
from .importlib import import_python_code
from .parser import Parser


class Compiler:
    """
    The compiler takes output from lexers/parsers and uses
    the resulting asts to create a model.
    """

    def __init__(self) -> None:
        self.context = CompilerContext("__main__")

    def compile(self, file: Path) -> None:
        """Compiles an Eikobot file given a path."""
        results = []
        self.context.set_path(file)
        import_python_code(["__main__"], file, self.context)

        for expr in Parser(file).parse():
            results.append(expr.compile(self.context))

    def reset(self) -> None:
        """Resets the compiler context for reuse."""
        self.context = CompilerContext("__main__")
