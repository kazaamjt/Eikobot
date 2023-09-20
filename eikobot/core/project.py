"""
A project differs from a module in that
a project is meant to be deployed.
It containes modules and a model.
"""
import sys
import tomllib
from pathlib import Path

from packaging import version
from pydantic import BaseModel, ValidationError

from .. import VERSION
from ..core import logger
from .package_manager import install_pkgs, install_py_deps


class ProjectSettings(BaseModel):
    """
    All possible settings read from an eiko.project file
    """

    exists: bool = False

    entry_point: str | None = None
    eikobot_version: str | None = None
    eikobot_requires: list[str] = []
    python_requires: list[str] = []
    dry_run: bool = False
    ssh_timeout: int = 3


def read_project() -> ProjectSettings:
    """
    Reads an eiko.toml file in the cwd and returns it as a settings object.
    """
    path = Path("eiko.toml")
    if not path.exists():
        return ProjectSettings()

    logger.debug("Reading eiko toml project file.")
    try:
        toml = tomllib.loads(Path("eiko.toml").read_text(encoding="utf-8"))
        project_toml = toml.get("eiko", {}).get("project")
        if project_toml is None:
            logger.debug("No project settings.")
            return ProjectSettings()

        return ProjectSettings(**project_toml, exists=True)
    except (tomllib.TOMLDecodeError, ValidationError) as e:
        logger.error(f"Failed to parse eiko.toml: {e}")
        sys.exit(1)


def eiko_version_match(  # pylint: disable=too-many-branches
    eikobot_version: str,
) -> bool:
    """
    Checks to see if the library is compatible with
    the currently installed version of eikobot.
    """
    if eikobot_version is None:
        return True

    eiko_version = version.parse(VERSION)
    for version_req in eikobot_version.split(","):
        if version_req.startswith(">="):
            if eiko_version < _parse_version(version_req[2:]):
                return False

        elif version_req.startswith("<="):
            if eiko_version > _parse_version(version_req[2:]):
                return False

        elif version_req.startswith("=="):
            if eiko_version != _parse_version(version_req[2:]):
                return False

        elif version_req.startswith("!="):
            if eiko_version == _parse_version(version_req[2:]):
                return False

        elif version_req.startswith(">"):
            if eiko_version <= _parse_version(version_req[1:]):
                return False

        elif version_req.startswith("<"):
            if eiko_version >= _parse_version(version_req[1:]):
                return False

        else:
            raise ValueError(
                f"Failed to parse eiko.toml eikobot_version option '{eikobot_version}'."
            )

    return True


def _parse_version(_version: str) -> version.Version:
    try:
        return version.parse(_version)
    except version.InvalidVersion as e:
        raise ValueError(f"failed to parse version `{_version}`.") from e


PROJECT_SETTINGS = read_project()
if PROJECT_SETTINGS.eikobot_version:
    try:
        if not eiko_version_match(PROJECT_SETTINGS.eikobot_version):
            logger.error(
                "Eikobot is not a matching version! "
                "".join(PROJECT_SETTINGS.eikobot_version)
            )
            sys.exit(1)
    except ValueError as err:
        logger.error(str(err))
        sys.exit(1)


async def init_project() -> None:
    """
    Initializes a project based on its eiko.toml settings.
    """
    logger.info("Initializing eikobot project.")
    if PROJECT_SETTINGS.exists:
        logger.info("Installing Project Python requirements.")
        install_py_deps(PROJECT_SETTINGS.python_requires)

        logger.info("Installing Project Eikobot requirements.")
        await install_pkgs(PROJECT_SETTINGS.eikobot_requires)
