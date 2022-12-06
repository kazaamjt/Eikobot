"""
The entrypoint to the client application.
Schould only contain things related to the client cli.
"""
import asyncio
import datetime
import sys
import time
import traceback
from pathlib import Path

import click

from .core import logger
from .core.compiler import Compiler
from .core.compiler.lexer import Token
from .core.compiler.misc import Index
from .core.deployer import Deployer
from .core.errors import EikoError, EikoPluginError
from .core.exporter import Exporter


@click.group()
@click.option("--debug", is_flag=True)
def cli(debug: bool = False) -> None:
    """
    The Eikobot CLI allows for compilation
    and exporting of eiko files.
    """
    log_level = logger.LOG_LEVEL.INFO
    if debug:
        log_level = logger.LOG_LEVEL.DEBUG
    logger.init(log_level=log_level)  # type: ignore


def print_error_trace(index: Index) -> None:
    """Using a given index, creates a nice CLI trace."""
    print(f'    File "{index.file.absolute()}", line {index.line + 1}')
    with open(index.file, "r", encoding="utf-8") as f:
        line = f.readlines()[index.line]
        clean_line = line.lstrip()
        diff = len(line) - len(clean_line)
        print(" " * 8 + clean_line.strip("\n"))
        print(" " * 8 + (index.col - diff) * " " + "^")


@cli.command(name="compile")
@click.option("-f", "--file", prompt="File", help="Path to entrypoint file.")
@click.option(
    "--output-model",
    is_flag=True,
    help="Outputs a human readable version of compiler context.",
)
@click.option(
    "--enable-plugin-stacktrace",
    is_flag=True,
    help="Outputs a plugins stacktrace if it raises an exception.",
)
def compile_cmd(
    file: str, output_model: bool = False, enable_plugin_stacktrace: bool = False
) -> None:
    """
    Compile an eikobot file.
    """
    _compile(file, output_model, enable_plugin_stacktrace)


def _compile(
    file: str, output_model: bool = False, enable_plugin_stacktrace: bool = False
) -> Compiler:
    start = time.time()
    pc_start = time.process_time()
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
            print_error_trace(e.index)

        if isinstance(e, EikoPluginError):
            if e.python_exception is not None:
                logger.error("Python error: " + str(e.python_exception))
                if enable_plugin_stacktrace:
                    logger.error("Python plugin stacktrace (ignore the first line):")
                    traceback.print_exception(e.python_exception)
                else:
                    logger.error(
                        "To view the python plugin stacktrace, use '--enable-plugin-stacktrace'"
                    )
        sys.exit(1)

    except NotImplementedError as e:
        logger.error("PANIC!! Compiler ran in to an unexpected error!")
        logger.error("Please report this error on github.")
        try:
            token = e.args[0]
            if isinstance(token, Token):
                logger.error("Got stuck here:")
                print_error_trace(token.index)
        except IndexError:
            pass
        sys.exit(1)

    if output_model:
        logger.info("resulting model context:")
        print(compiler.context)

    time_taken = time.time() - start
    time_taken_formatted = str(datetime.timedelta(seconds=time_taken))
    pc_time_taken = time.process_time() - pc_start
    pc_time_taken_formatted = str(datetime.timedelta(seconds=pc_time_taken))
    logger.info(
        f"Compiled in {time_taken_formatted} "
        f"(Process time: {pc_time_taken_formatted})"
    )

    return compiler


@cli.command()
@click.option("-f", "--file", prompt="File", help="Path to entrypoint file.")
@click.option(
    "--enable-plugin-stacktrace",
    is_flag=True,
    help="Outputs a plugins stacktrace if it raises an exception.",
)
def deploy(file: str, enable_plugin_stacktrace: bool = False) -> None:
    """
    Compile, export and deploy a model from a given file.
    """
    start = time.time()
    compiler = _compile(file, False, enable_plugin_stacktrace)
    logger.info("Exporting model.")
    exporter = Exporter()
    exporter.export_from_context(compiler.context)
    logger.info("Deploying model.")
    deployer = Deployer()
    asyncio.run(deployer.deploy(exporter.base_tasks))

    time_taken = time.time() - start
    time_taken_formatted = str(datetime.timedelta(seconds=time_taken))
    logger.info(f"Deployed in {time_taken_formatted}")


if __name__ == "__main__":
    cli()
