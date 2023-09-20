"""
The entrypoint to the client application.
Schould only contain things related to the client cli.
"""
import asyncio
import datetime
import signal
import subprocess
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
from .core.project import PROJECT_SETTINGS, init_project


@click.group()
@click.option("--debug", is_flag=True)
@click.version_option(VERSION)
def cli(debug: bool = False) -> None:
    """
    The Eikobot CLI allows for compilation
    and exporting of eiko files.
    """
    log_level = logger.LogLevel.INFO
    if debug:
        log_level = logger.LogLevel.DEBUG
    logger.init(log_level=log_level)


@cli.command(name="compile")
@click.option("-f", "--file", "file", help="Path to entrypoint file.")
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
    file: str | None, output_model: bool = False, enable_plugin_stacktrace: bool = False
) -> None:
    """
    Compile an eikobot file.
    """
    _compile(file, output_model, enable_plugin_stacktrace)


def _get_file_path(file: str | None) -> Path:
    if file is None:
        if PROJECT_SETTINGS.entry_point is None:
            file = ""
            while file == "":
                file = input("File: ")
        else:
            file = PROJECT_SETTINGS.entry_point

    return Path(file)


def _compile(
    file: str | None, output_model: bool = False, enable_plugin_stacktrace: bool = False
) -> Compiler:
    file_path = _get_file_path(file)

    start = time.time()
    pc_start = time.process_time()
    compiler = Compiler()

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
@click.option("-f", "--file", "file", help="Path to entrypoint file.")
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
@click.option(
    "--force",
    is_flag=True,
    help="Overwrites ignores any dry-run parameters",
)
def deploy(
    file: str | None,
    enable_plugin_stacktrace: bool = False,
    dry_run: bool = False,
    force: bool = False,
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
        deployer = Deployer()
        if (dry_run or PROJECT_SETTINGS.dry_run) and not force:
            logger.info("Performing dry run.")
            asyncio.run(deployer.dry_run(exporter))
        else:
            logger.info("Deploying model.")
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
    if target == ".":
        requires: list[str] = []
        _pkg_data_path = Path("eiko.toml")
        if _pkg_data_path.exists():
            try:
                pkg_data = package_manager.read_pkg_toml(_pkg_data_path)
                requires.extend(pkg_data.eikobot_requires)
                if pkg_data.python_requires:
                    package_manager.install_py_deps(pkg_data.python_requires)
            except EikoError:
                pass

        if len(requires) > 0:
            asyncio.run(package_manager.install_pkgs(requires))
        elif not pkg_data.python_requires:
            logger.error("No requirements found.")

    else:
        asyncio.run(_install_pkg(target))


async def _install_pkg(target: str) -> None:
    try:
        await package_manager.install_pkg(target)
    except EikoError as e:
        logger.error(str(e))


@package.command(name="list")
def list_pkg() -> None:
    """
    Lists all installed packages.
    """
    packages = package_manager.get_pkg_index()
    for pkg in packages.values():
        print(f"{pkg.name}=={pkg.version}")


@package.group()
def release() -> None:
    pass


@release.command()
def github() -> None:
    """
    Creates a release
    """
    try:
        asyncio.run(package_manager.create_github_release())
    except EikoError as e:
        logger.error(str(e))


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


@cli.group()
def project() -> None:
    pass


@project.command()
def init() -> None:
    """
    Initialize an existing project.
    """
    if PROJECT_SETTINGS.exists:
        asyncio.run(init_project())
    else:
        logger.error("CWD does not have an eiko.toml file.")


def _run_wrapped() -> None:
    # There is a problem with relative imports in python code
    # when we import python code from eiko modules/packages at runtime.
    # This bug only happens if we are not pythons main entrypoint.
    # In other words this is a pretty ugly hack, and I do not know
    # any otehr fixes at this point.
    with subprocess.Popen(
        [
            "python",
            "-m",
            "eikobot",
            *sys.argv[1:],
        ],
    ) as _process:
        try:
            _process.wait()
        except KeyboardInterrupt:
            _process.send_signal(signal.SIGINT)

        sys.exit(_process.returncode)


def main() -> None:
    """
    Python entrypoint function that does some housekeeping.
    """
    if __name__ == "__main__":
        cli()
    else:
        _run_wrapped()


if __name__ == "__main__":
    main()
