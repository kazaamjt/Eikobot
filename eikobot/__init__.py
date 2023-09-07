"""
Eikobot helps you create and maintain your infrastructure
in a gitops way.
"""
import sys
import tomllib
from pathlib import Path

import pkg_resources
from packaging import version
from pydantic import BaseModel, ValidationError

from .core import logger

VERSION = pkg_resources.require("eikobot")[0].version


class ProjectSettings(BaseModel):
    """
    All possible settings read from an eiko.project file
    """

    dry_run: bool = False
    eikobot_version: str | None = None
    eikobot_requires: list[str] = []
    python_requires: list[str] = []


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

        return ProjectSettings(**project_toml)
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
