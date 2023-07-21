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

from . import VERSION
from .core import logger, package_manager
from .core.compiler import Compiler
from .core.compiler.lexer import Token
from .core.deployer import Deployer
from .core.errors import EikoError, EikoPluginError
from .core.exporter import Exporter


@click.group()
@click.option("--debug", is_flag=True)
@click.version_option(VERSION)
def cli(debug: bool = False) -> None:
    """
    The Eikobot CLI allows for compilation
    and exporting of eiko files.
    """
    log_level = logger.LOG_LEVEL.INFO
    if debug:
        log_level = logger.LOG_LEVEL.DEBUG
    logger.init(log_level=log_level)  # type: ignore


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
            logger.print_error_trace(e.index)

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
                logger.print_error_trace(token.index)
        except IndexError:
            pass
        sys.exit(1)

    if output_model:
        logger.info("resulting model context:")
        print(compiler.context)

    pc_time_taken = time.process_time() - pc_start
    time_taken = time.time() - start
    pc_time_taken_formatted = str(datetime.timedelta(seconds=pc_time_taken))
    time_taken_formatted = str(datetime.timedelta(seconds=time_taken))
    logger.info(
        f"Compiled in {time_taken_formatted} 🤖 "
        f"(Process time: {pc_time_taken_formatted})"
    )

    return compiler


@cli.command()
@click.option("-f", "--file", "file", prompt="File", help="Path to entrypoint file.")
@click.option(
    "--enable-plugin-stacktrace",
    is_flag=True,
    help="Outputs a plugins stacktrace if it raises an exception.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Does a dry run of all the tasks in a given model.",
)
def deploy(
    file: str,
    enable_plugin_stacktrace: bool = False,
    dry_run: bool = False,
) -> None:
    """
    Compile, export and deploy a model from a given file.
    """
    start = time.time()
    compiler = _compile(file, False, enable_plugin_stacktrace)
    logger.info("Exporting model.")
    try:
        exporter = Exporter()
        exporter.export_from_context(compiler.context)
        logger.info("Deploying model.")
        deployer = Deployer()
        if dry_run:
            asyncio.run(deployer.dry_run(exporter))
        else:
            asyncio.run(deployer.deploy(exporter, log_progress=True))
    except EikoError as e:
        logger.error(str(e))

        if e.index is not None:
            logger.print_error_trace(e.index)
    else:
        if deployer.failed:
            logger.error(
                "Failed to deploy model. "
                f"({deployer.progress.done} out of {deployer.progress.total} tasks done)"
            )
        else:
            time_taken = time.time() - start
            time_taken_formatted = str(datetime.timedelta(seconds=time_taken))
            logger.info(f"Deployed in {time_taken_formatted} 🤖")


@cli.group()
def package() -> None:
    pass


@package.command(name="build")
def build_pkg() -> None:
    """Builds a package in the cwd, using an eiko.toml file."""
    try:
        package_manager.build_pkg()
    except EikoError as e:
        logger.error(str(e))


@package.command(name="install")
@click.argument("target")
def install_pkg(target: str) -> None:
    """
    Install a package from different sources.
    """
    try:
        package_manager.install_pkg(target)
    except EikoError as e:
        logger.error(str(e))


@package.command(name="list")
def list_pkg() -> None:
    """
    Lists all installed packages.
    """
    packages = package_manager.get_installed_pkg()
    for pkg in packages.values():
        print(f"{pkg.name}=={pkg.version}")


@package.command(name="uninstall")
@click.argument("name")
def uninstall_pkg(name: str) -> None:
    """
    Performs all required steps to delete a package.
    """
    try:
        package_manager.uninstall_pkg(name)
    except EikoError as e:
        logger.error(str(e))


if __name__ == "__main__":
    cli()
