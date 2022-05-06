"""
The entrypoint to the client application.
Schould only contain things related to the client cli.
"""
import sys
from pathlib import Path

import click

from .core import logger
from .core.compiler import Compiler
from .core.compiler.errors import EikoError


@click.group()
@click.option("--debug", is_flag=True)
def cli(debug: bool = False) -> None:
    """Directly call the Eikobot compiler."""
    log_level = logger.LOG_LEVEL.INFO
    if debug:
        log_level = logger.LOG_LEVEL.DEBUG
    logger.init(log_level=log_level)  # type: ignore


@cli.command()
@click.option("-f", "--file", prompt="File", help="Path to entrypoint file.")
def compile(file: str) -> None:  # pylint: disable=redefined-builtin
    """
    Compile an eikobot file.
    """
    compiler = Compiler()

    file_path = Path(file)
    if not file_path.exists():
        logger.error(f"No such file: {file_path}")
        sys.exit(1)

    logger.info(f"Compiling {file_path}")
    try:
        compiler.compile(file_path)
    except EikoError as e:
        logger.error(str(e))
        if e.index is not None:
            print(f"    File {e.index.file.absolute()}, line {e.index.line}")
            with open(e.index.file, "r", encoding="utf-8") as f:
                line = f.readlines()[e.index.line]
                clean_line = line.lstrip()
                diff = len(line) - len(clean_line)
                print(" " * 8 + clean_line.strip("\n"))
                print(" " * 8 + (e.index.col - diff) * " " + "^")

    logger.info("Model result:")
    print(compiler.context)


if __name__ == "__main__":
    cli()
