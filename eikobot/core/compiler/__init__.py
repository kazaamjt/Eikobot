from pathlib import Path

from .definitions.context import CompilerContext
from .parser import Parser


class Compiler:
    """
    The compiler takes output from lexers/parsers and uses
    the resulting asts to create a model.
    """

    def __init__(self) -> None:
        self.context = CompilerContext(
            "__main__",
        )

    def compile(self, file: Path) -> None:
        parser = Parser(file)
        for expr in parser.parse():
            expr.compile(self.context)
