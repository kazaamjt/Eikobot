"""
For help with creating, distributing and installing packages.
"""
import asyncio
import copy
import os
import shutil
import subprocess
import sys
import tarfile
import tomllib
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import aiohttp
from packaging import version
from pydantic import BaseModel, ValidationError

from ... import VERSION
from .. import human_readable, logger
from ..compiler.importlib import INTERNAL_LIB_PATH
from ..errors import EikoError

CACHE_PATH = Path(__file__).parent / "cache"
CACHE_PATH.mkdir(exist_ok=True)
LIB_PATH = Path(__file__).parent / "lib"
LIB_PATH.mkdir(exist_ok=True)

PKG_INDEX: dict[str, "PackageData"] = {}


class EikoPackageError(EikoError):
    """An error that occured during the eiko compilation process."""

    def __init__(self, reason: str, *args: object) -> None:
        super().__init__(reason, *args)


class PackageData(BaseModel):
    """
    All the settings one might
    find in an eiko.toml file.
    """

    name: str
    source_dir: Path
    version: Optional[str] = None
    description: Optional[str] = None
    long_description: Optional[str] = None
    long_description_content_type: Optional[str] = None
    author: Optional[str] = None
    author_email: Optional[str] = None
    license: Optional[str] = None
    eikobot_requires: Optional[str] = None
    requires: list[str] = []

    def pkg_name_version(self) -> str:
        """
        Returns the name that was used for the install dir
        under package_manager/lib.
        """
        name = self.name
        if self.version is not None:
            name += "-" + self.version

        return name

    def eiko_version_match(self) -> bool:  # pylint: disable=too-many-branches
        """
        Checks to see if the library is compatible with
        the currently installed version of eikobot.
        """
        if self.eikobot_requires is None:
            return True

        eiko_version = version.parse(VERSION)
        for version_req in self.eikobot_requires.split(","):
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
                raise EikoPackageError(
                    f"Failed to parse eiko.toml option eikobot_requires '{self.eikobot_requires}'."
                )

        return True


def _parse_version(_version: str) -> version.Version:
    try:
        return version.parse(_version)
    except version.InvalidVersion as e:
        raise EikoPackageError(
            f"failed to parse `eikobot_requires` version `{_version}`"
        ) from e


def _construct_pkg_index() -> None:
    for pkg_dir in LIB_PATH.glob("*"):
        pkg_data = _read_pkg_toml(pkg_dir / "eiko.toml")
        PKG_INDEX[pkg_data.name] = pkg_data


def _read_pkg_toml(path: Path) -> PackageData:
    logger.debug("Reading eiko toml file.")
    toml = tomllib.loads(path.read_text(encoding="utf-8"))
    pkg_toml = toml.get("eiko", {}).get("package")
    if pkg_toml is None:
        raise EikoPackageError("eiko.toml does not contain an 'eiko.package' section.")
    try:
        pkg_data = PackageData(**pkg_toml)
    except ValidationError as e:
        raise EikoPackageError(f"Failed to parse eiko.toml: {e}") from e

    return pkg_data


def build_pkg() -> None:
    """Builds a package in the cwd"""
    logger.info("Building package.")
    eiko_toml_path = Path("eiko.toml")
    if not eiko_toml_path.exists():
        raise EikoPackageError("eiko.toml file missing.")

    pkg_data = _read_pkg_toml(eiko_toml_path)
    dist = Path("dist")
    dist.mkdir(exist_ok=True)
    if not pkg_data.source_dir.exists():
        raise EikoPackageError(f"Not such source directory: '{pkg_data.source_dir}'.")

    if not pkg_data.source_dir.is_dir():
        raise EikoPackageError(f"'{pkg_data.source_dir}' is not a directory.")

    logger.debug("Setting up build env.")
    build_dir = dist / "build"
    shutil.rmtree(build_dir, ignore_errors=True)
    build_dir.mkdir()
    # Compile every file here to make sure they are valid?
    # This would also be the place to check for dangerous sources.
    shutil.copytree(
        pkg_data.source_dir,
        build_dir / pkg_data.source_dir,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    shutil.copy(eiko_toml_path, build_dir)

    logger.debug("Creating tar archive.")
    dist_name = pkg_data.pkg_name_version()
    dist_file_name = dist_name + ".eiko.tar.gz"
    dist_file = dist / dist_file_name

    with tarfile.open(dist_file, "w:gz") as archive:
        archive.add(build_dir, arcname=dist_name)

    logger.debug("cleaning up build env.")
    shutil.rmtree(build_dir, ignore_errors=True)

    logger.info(f"Build package '{dist_name}'")


def install_pkg(pkg_def: str) -> None:
    """
    This functions gets a string prompt and will try to figure out
    if the package is http(s), git or a path.
    """
    _construct_pkg_index()
    if pkg_def.startswith("http://") or pkg_def.startswith("https://"):
        _download_pkg(pkg_def)

    elif pkg_def.endswith(".eiko.tar.gz"):
        _install_pkg_from_path(Path(pkg_def))

    else:
        raise EikoPackageError("Failed to properly parse package url or path.")


def _download_pkg(url: str) -> None:
    if url.endswith(".eiko.tar.gz"):
        logger.debug("Directly downloading package.")
        asyncio.run(_download_to_cache(url))

    else:
        raise EikoPackageError(
            "Currently only direct links to an eiko package are supported."
        )


async def _download_to_cache(url: str) -> None:
    pkg_path = CACHE_PATH / Path(urlparse(url).path).name
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as session:
        logger.info(f"Fetching {url}")
        try:
            response = await session.get(url)
            total_dl_size = int(response.headers.get("CONTENT-LENGTH", 0))
            downloaded = 0

            with open(pkg_path, "wb") as f:
                async for data, _ in response.content.iter_chunks():
                    f.write(data)
                    downloaded += sys.getsizeof(data)
                    percent = int((downloaded / total_dl_size) * 20)
                    pg_bar = "=" * percent
                    if percent == 20:
                        print(
                            f"    [{pg_bar}]",
                            f"{human_readable(total_dl_size)}/{human_readable(total_dl_size)}",
                        )
                    else:
                        print(
                            f"    [{pg_bar}>{(20 - percent - 1) * ' '}]",
                            f"{human_readable(downloaded)}/{human_readable(total_dl_size)}",
                            end="\r",
                        )

        except aiohttp.ClientError as e:
            raise EikoPackageError(f"Failed to download {url}: {e}") from e

    _install_pkg_from_cache(pkg_path.name)


def _install_pkg_from_path(pkg_path: Path) -> None:
    """
    Install a package using a path to an .eiko.tar.gz file.
    """
    if not pkg_path.exists():
        raise EikoPackageError(f"Package path does not exist: '{pkg_path}'.")
    logger.debug("Adding archive to cache.")
    shutil.copy(pkg_path, CACHE_PATH)
    _install_pkg_from_cache(pkg_path.name)


def _install_pkg_from_cache(archive_name: str) -> None:
    pkg_name = archive_name.removesuffix(".eiko.tar.gz")
    logger.debug("Unpacking archive.")
    with tarfile.open(CACHE_PATH / archive_name, "r:gz") as archive:
        archive.extractall(LIB_PATH)

    pkg_lib_path = LIB_PATH / pkg_name
    pkg_data = _read_pkg_toml(pkg_lib_path / "eiko.toml")
    prev_pkg = PKG_INDEX.get(pkg_data.name)
    if prev_pkg is not None:
        _uninstall_pkg(prev_pkg)

    with tarfile.open(CACHE_PATH / archive_name, "r:gz") as archive:
        archive.extractall(LIB_PATH)

    if pkg_data.version is None:
        logger.debug(f"Installing '{pkg_data.name}'.")
    else:
        logger.debug(f"Installing '{pkg_data.name}=={pkg_data.version}'.")

    requirements_file = pkg_lib_path / "requirements.txt"
    if requirements_file.exists():
        logger.debug("Installing python requirements.")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", requirements_file],
            check=True,
        )

    logger.debug("Installing requirements.")
    for req in pkg_data.requires:
        install_pkg(req)

    try:
        shutil.copytree(
            pkg_lib_path / pkg_data.source_dir,
            INTERNAL_LIB_PATH / pkg_data.source_dir,
            dirs_exist_ok=False,
        )
    except FileExistsError:
        # This is a bug in the package index
        # I have no idea what causes it, but this is hack around the issue.
        os.remove(INTERNAL_LIB_PATH / pkg_data.source_dir)
        os.symlink(
            pkg_lib_path / pkg_data.source_dir, INTERNAL_LIB_PATH / pkg_data.source_dir
        )

    if pkg_data.version is None:
        logger.info(f"Installed '{pkg_data.name}'.")
    else:
        logger.info(f"Installed '{pkg_data.name}=={pkg_data.version}'.")


def get_installed_pkg() -> dict[str, PackageData]:
    _construct_pkg_index()
    return copy.deepcopy(PKG_INDEX)


def uninstall_pkg(name: str) -> None:
    """
    Uninstalls a package.
    """
    _construct_pkg_index()
    pkg_data = PKG_INDEX.get(name)
    if pkg_data is None:
        logger.error(f"Failed to install package: '{name}'")
        return

    _uninstall_pkg(pkg_data)


def _uninstall_pkg(pkg_data: PackageData) -> None:
    logger.debug(f"Uninstalling '{pkg_data.pkg_name_version()}'")
    try:
        shutil.rmtree(INTERNAL_LIB_PATH / pkg_data.source_dir)
    except FileNotFoundError:
        pass

    shutil.rmtree(LIB_PATH / pkg_data.pkg_name_version())
    logger.info(f"Uninstalled '{pkg_data.pkg_name_version()}'")
