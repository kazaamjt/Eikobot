from pathlib import Path

from .parser import Parser


class Compiler:
    """
    The compiler takes output from lexers/parsers and uses
    the resulting asts to create a model.
    """

    def __init__(self) -> None:
        pass

    def compile(self, file: Path) -> None:
        parser = Parser(file)
        for expr in parser.parse():
            pass
