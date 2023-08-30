"""
Eikobot helps you create and maintain your infrastructure
in a gitops way.
"""
import sys
import tomllib
from pathlib import Path

import pkg_resources
from pydantic import BaseModel, ValidationError

from .core import logger

VERSION = pkg_resources.require("eikobot")[0].version


class ProjectSettings(BaseModel):
    """
    All possible settings read from an eiko.project file
    """

    dry_run: bool = False
    requires: list[str] = []


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


PROJECT_SETTINGS = read_project()
