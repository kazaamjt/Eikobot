import sys
from pathlib import Path

import click

from .core import logging
from .core.compiler import Compiler


@click.group()
def cli() -> None:
    logging.init()


@cli.command()
@click.option("-f", "--file", prompt="File", help="Path to entrypoint file.")
def compile(file: str) -> None:  # pylint: disable=redefined-builtin
    compiler = Compiler()

    file_path = Path(file)
    if not file_path.exists():
        logging.error(f"No such file: {file_path}")
        sys.exit(1)

    logging.info(f"Compiling {file_path}")
    compiler.compile(file_path)
    print(compiler.context.assigned)


if __name__ == "__main__":
    cli()
