import json
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

    print_dict = {}
    for var, eiko_obj in compiler.context.assigned.items():
        print_dict[f"{var} [{eiko_obj.type}]"] = eiko_obj.printable()

    print("model =", json.dumps(print_dict, indent=2))


if __name__ == "__main__":
    cli()
