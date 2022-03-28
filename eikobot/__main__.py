"""
The entrypoint to the client application.
Schould only contain things related to the client cli.
"""
import sys
from pathlib import Path

import click

from .core import logging
from .core.compiler import Compiler
from .core.compiler.errors import EikoError


@click.group()
def cli() -> None:
    logging.init()


@cli.command()
@click.option("-f", "--file", prompt="File", help="Path to entrypoint file.")
def compile(file: str) -> None:  # pylint: disable=redefined-builtin
    """
    Compile an eikobot file.
    """
    compiler = Compiler()

    file_path = Path(file)
    if not file_path.exists():
        logging.error(f"No such file: {file_path}")
        sys.exit(1)

    logging.info(f"Compiling {file_path}")
    try:
        compiler.compile(file_path)
    except EikoError as e:
        logging.error(str(e))
        if e.index is not None:
            print(f"    File {e.index.file.absolute()}, line {e.index.line}")
            with open(e.index.file, "r", encoding="utf-8") as f:
                line = f.readlines()[e.index.line]
                clean_line = line.lstrip()
                diff = len(line) - len(clean_line)
                print(" " * 8 + clean_line.strip("\n"))
                print(" " * 8 + (e.index.col - diff) * " " + "^")

    print(compiler.context.storage)


if __name__ == "__main__":
    cli()
