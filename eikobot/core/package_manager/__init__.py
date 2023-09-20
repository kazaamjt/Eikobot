"""
For help with creating, distributing and installing packages.
"""
import asyncio
import copy
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import aiohttp
from packaging import version
from pydantic import BaseModel, ValidationError

from .. import human_readable, logger
from ..compiler.importlib import INTERNAL_LIB_PATH
from ..errors import EikoError

CACHE_PATH = Path(__file__).parent / "cache"
CACHE_PATH.mkdir(exist_ok=True)
LIB_PATH = Path(__file__).parent / "lib"
LIB_PATH.mkdir(exist_ok=True)

PKG_INDEX_PATH = Path(__file__).parent / "index.json"

GH_HEADERS = {
    "X-GitHub-Api-Version": "2022-11-28",
    "Accept": "application/vnd.github+json",
}
GH_TOKEN = os.environ.get("GITHUB_TOKEN", None)
if GH_TOKEN is not None:
    GH_HEADERS["Authorization"] = f"Bearer {GH_TOKEN}"


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
    version: str | None = None
    description: str | None = None
    long_description: str | None = None
    long_description_content_type: str | None = None
    author: str | None = None
    author_email: str | None = None
    license: str | None = None
    eikobot_version: str | None = None
    eikobot_requires: list[str] = []
    python_requires: list[str] = []
    github_name: str | None = None

    def pkg_name_version(self) -> str:
        """
        Returns the name that was used for the install dir
        under package_manager/lib.
        """
        name = self.name
        if self.version is not None:
            name += "-" + self.version

        return name


def get_pkg_index() -> dict[str, "PackageData"]:
    """
    Constructs the package index and returns it
    """
    pkg_index: dict[str, "PackageData"] = {}
    for pkg_dir in LIB_PATH.glob("*"):
        pkg_data = read_pkg_toml(pkg_dir / "eiko.toml")
        pkg_index[pkg_data.name] = pkg_data

    return pkg_index


def read_pkg_toml(path: Path) -> PackageData:
    """
    Reads a toml and returns it's settings as python object.
    """
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


def build_pkg(pkg_data: PackageData | None = None) -> Path:
    """Builds a package in the cwd"""
    logger.info("Building package.")
    eiko_toml_path = Path("eiko.toml")
    if pkg_data is None:
        if not eiko_toml_path.exists():
            raise EikoPackageError("eiko.toml file missing.")
        pkg_data = read_pkg_toml(eiko_toml_path)

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
    return dist_file


async def install_pkg(pkg_def: str) -> None:
    """
    This functions gets a string prompt and will try to figure out
    if the package is http(s), git or a path.
    """
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as session:
        if pkg_def.startswith("http://") or pkg_def.startswith("https://"):
            await _download_pkg(pkg_def, session)

        elif pkg_def.startswith("GH://"):
            await _download_pkg_gh(pkg_def, session)

        elif pkg_def.endswith(".eiko.tar.gz"):
            await _install_pkg_from_path(Path(pkg_def))

        else:
            raise EikoPackageError("Failed to properly parse package url or path.")


async def _download_pkg(url: str, session: aiohttp.ClientSession) -> None:
    if url.endswith(".eiko.tar.gz"):
        await _download_to_cache(url, session)

    else:
        raise EikoPackageError(
            "Currently only direct links to an eiko package are supported."
        )


def _get_gh_package(github_name: str) -> PackageData | None:
    pkg_index = get_pkg_index()
    for package in pkg_index.values():
        if (
            package.github_name is not None
            and package.github_name.lower() == github_name.lower()
        ):
            return package

    return None


@dataclass
class GHAsset:
    name: str
    url: str


async def _download_pkg_gh(pkg_def: str, session: aiohttp.ClientSession) -> None:
    """
    Download a package straight from github, without extra fuzz.
    """
    logger.debug(f"[{pkg_def}] Parsing github link.")
    _pkg_def = pkg_def.replace("GH://", "")
    _version: version.Version | None = None
    if "==" in _pkg_def:
        _pkg_def, _version = _parse_pkg_version("GH://", _pkg_def)

    prev_pkg = _get_gh_package(_pkg_def)
    if prev_pkg is not None:
        if _version is None or (
            prev_pkg.version is not None and version.parse(prev_pkg.version) == _version
        ):
            logger.info(f"Package '{_pkg_def}' already installed.")
            return

        _uninstall_pkg(prev_pkg)

    assets = await _get_gh_assets(
        f"https://api.github.com/repos/{_pkg_def}", pkg_def, session
    )

    if len(assets) == 0:
        raise EikoPackageError(f"Github package '{pkg_def}' has no releases or assets.")

    pkg: GHAsset | None = None
    _, pkg_name = _pkg_def.split("/")
    if _version is None:
        pkg = assets[0]

    else:
        for asset in assets:
            if pkg_name.lower() in asset.name.lower() and str(_version) in asset.name:
                pkg = asset
                break

    if pkg is None:
        raise EikoPackageError(f"No package that matches '{pkg_def}' was found.")

    await _download_pkg(pkg.url, session)


def _parse_pkg_version(protocol: str, pkg_def: str) -> tuple[str, version.Version]:
    try:
        _pkg_def, unparsed_version = pkg_def.split("==")
        return _pkg_def, version.parse(unparsed_version)
    except version.InvalidVersion as e:
        raise EikoPackageError(
            f"failed to parse package version `{unparsed_version}`."
        ) from e
    except ValueError as e:
        raise EikoPackageError(f"Failed to parse '{protocol}{pkg_def}'.") from e


async def _get_gh_assets(
    gh_url: str,
    pkg_def: str,
    session: aiohttp.ClientSession,
) -> list[GHAsset]:
    logger.debug(f"[{pkg_def}] Getting github releases.")
    releases_resp = await session.get(gh_url + "/releases", headers=GH_HEADERS)
    if 200 < releases_resp.status > 299:
        await session.close()
        raise EikoPackageError(
            f"Repo not found on github: '{pkg_def}'. (HTTP {releases_resp.status})"
        )

    releases = await releases_resp.json()
    if len(releases) == 0:
        return []

    logger.debug(f"[{pkg_def}] Getting github assets.")
    assets: list[GHAsset] = []
    for release in releases:
        assets_resp = await session.get(release["assets_url"])
        unparsed_assets = await assets_resp.json()
        for _asset in unparsed_assets:
            assets.append(GHAsset(_asset["name"], _asset["browser_download_url"]))

    return assets


async def _download_to_cache(url: str, session: aiohttp.ClientSession) -> None:
    pkg_path = CACHE_PATH / Path(urlparse(url).path).name
    if not pkg_path.exists():
        try:
            response = await session.get(url)
            dl_size = int(response.headers.get("CONTENT-LENGTH", 0))
            logger.info(f"Fetching '{url}' [{human_readable(dl_size)}]")

            with open(pkg_path, "wb") as f:
                async for data, _ in response.content.iter_chunks():
                    f.write(data)

            logger.debug(f"Downloaded {human_readable(dl_size)}.")

        except aiohttp.ClientError as e:
            raise EikoPackageError(f"Failed to download {url}: {e}") from e
    else:
        logger.debug(f"Using cached version of '{pkg_path.name}'.")

    await _install_pkg_from_cache(pkg_path.name)


async def _install_pkg_from_path(pkg_path: Path) -> None:
    """
    Install a package using a path to an .eiko.tar.gz file.
    """
    if not pkg_path.exists():
        raise EikoPackageError(f"Package path does not exist: '{pkg_path}'.")
    logger.debug("Adding archive to cache.")
    shutil.copy(pkg_path, CACHE_PATH)
    await _install_pkg_from_cache(pkg_path.name)


async def _install_pkg_from_cache(archive_name: str) -> None:
    pkg_name = archive_name.removesuffix(".eiko.tar.gz")
    pkg_index = get_pkg_index()
    if (LIB_PATH / archive_name).exists():
        logger.debug("Archive is already unpacked.")

    else:
        logger.debug("Unpacking archive.")
        with tarfile.open(CACHE_PATH / archive_name, "r:gz") as archive:
            archive.extractall(LIB_PATH)

    pkg_lib_path = LIB_PATH / pkg_name
    pkg_data = read_pkg_toml(pkg_lib_path / "eiko.toml")
    prev_pkg = pkg_index.get(pkg_data.name)
    if prev_pkg is not None:
        if pkg_data.version != prev_pkg.version or pkg_data.version is None:
            _uninstall_pkg(prev_pkg)
        else:
            logger.info(
                f"Package '{pkg_data.name}=={pkg_data.version}' already installed."
            )
            return

    if pkg_data.version is None:
        logger.debug(f"Installing '{pkg_data.name}'.")
    else:
        logger.debug(f"Installing '{pkg_data.name}=={pkg_data.version}'.")

    install_py_deps(pkg_data.python_requires)

    logger.debug(f"Installing requirements for '{pkg_name}'.")
    await install_pkgs(pkg_data.eikobot_requires)

    try:
        shutil.copytree(
            pkg_lib_path / pkg_data.source_dir,
            INTERNAL_LIB_PATH / pkg_data.source_dir,
            dirs_exist_ok=False,
        )
    except FileExistsError:
        # This is a bug in the package index
        # I have no idea what causes it, but this is a hack around the issue.
        os.remove(INTERNAL_LIB_PATH / pkg_data.source_dir)
        os.symlink(
            pkg_lib_path / pkg_data.source_dir, INTERNAL_LIB_PATH / pkg_data.source_dir
        )

    if pkg_data.version is None:
        logger.info(f"Installed '{pkg_data.name}'.")
    else:
        logger.info(f"Installed '{pkg_data.name}=={pkg_data.version}'.")


def install_py_deps(deps: list[str]) -> None:
    """
    Install Python dependencies using pip running in a subprocess.
    """
    logger.debug("Installing python requirements.")
    if logger.LOG_LEVEL == logger.LogLevel.DEBUG:
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "install", *deps],
            check=False,
        )
    else:
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "install", *deps],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    if proc.returncode != 0:
        logger.error(f"'pip install {' '.join(deps)}' failed.")
        if logger.LOG_LEVEL != logger.LogLevel.DEBUG:
            print(proc.stderr.decode())

        sys.exit(1)


def uninstall_pkg(name: str) -> None:
    """
    Uninstalls a package.
    """
    pkg_data = get_pkg_index().get(name)
    if pkg_data is None:
        logger.error(f"Package not found: '{name}'")
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


async def install_pkgs(pkg_list: list[str]) -> None:
    for pkg in pkg_list:
        await install_pkg(pkg)


async def create_github_release() -> None:
    """
    Does the follozing in order:
    - Checks to make sure the version doesn't exist on Github
    - Builds the package
    - Tags it on the git tree and pushes the tags
    - Creates a release on Github
    - Uploads the package as a release asset
    """
    if GH_TOKEN is None:
        raise EikoPackageError("Environment variable 'GITHUB_TOKEN' must be set.")

    logger.info("Releasing to github.")
    eiko_toml_path = Path("eiko.toml")
    if not eiko_toml_path.exists():
        raise EikoPackageError("eiko.toml file missing.")
    pkg_data = read_pkg_toml(eiko_toml_path)

    if pkg_data.github_name is None:
        raise EikoPackageError("'github_name' must be set in eiko.toml.")
    owner, repo = pkg_data.github_name.split("/")

    if pkg_data.version is None:
        raise EikoPackageError("'version' must be set in eiko.toml.")

    git_status = await asyncio.subprocess.create_subprocess_shell(
        "git status --porcelain",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await git_status.communicate()
    if stdout.decode():
        raise EikoPackageError("Git tree is not clean!\n" + stdout.decode())

    logger.debug("Checking github repo for existing packages.")
    session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10))
    gh_assets = await _get_gh_assets(
        f"https://api.github.com/repos/{pkg_data.github_name}",
        pkg_data.github_name,
        session,
    )

    for asset in gh_assets:
        if pkg_data.version in asset.name:
            await session.close()
            raise EikoPackageError(
                f"A release with version number '{pkg_data.version}' "
                "already exists on Github."
            )

    archive = build_pkg(pkg_data)
    logger.info("Creating git tags.")
    await _git_tag_and_push(pkg_data)

    logger.info("Creating release on github and uploading data.")
    release_url = await _create_gh_release(owner, repo, pkg_data, session)
    await _upload_gh_asset(archive, release_url, session)

    await session.close()
    logger.info("Successfully created release!")


async def _git_tag_and_push(pkg_data: PackageData) -> None:
    await asyncio.subprocess.create_subprocess_shell(
        f"git tag {pkg_data.version}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await asyncio.subprocess.create_subprocess_shell(
        f"git tag v{pkg_data.version}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await asyncio.subprocess.create_subprocess_shell(
        "git push --tags",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


async def _create_gh_release(
    owner: str,
    repo: str,
    pkg_data: PackageData,
    session: aiohttp.ClientSession,
) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    data = {
        "owner": owner,
        "repo": repo,
        "tag_name": pkg_data.version,
        "name": f"v{pkg_data.version}",
        "draft": False,
        "prerelease": False,
        "generate_release_notes": False,
    }
    headers = {
        **GH_HEADERS,
        "content-type": "application/json",
    }
    response = await session.post(
        url,
        data=json.dumps(data),
        headers=headers,
    )
    if 200 < response.status > 299:
        await session.close()
        raise EikoPackageError(
            "Failed to create a release on Github. "
            f"(HTTP {response.status}: {await response.text()})"
        )

    return (await response.json())["url"]  # type: ignore


async def _upload_gh_asset(
    asset: Path, release_url: str, session: aiohttp.ClientSession
) -> None:
    url = release_url.replace("api.github.com", "uploads.github.com")
    url += f"/assets?name={asset.name}"
    response = await session.post(url, data=asset.read_bytes(), headers=GH_HEADERS)
    if 200 < response.status > 299:
        await session.close()
        raise EikoPackageError(
            "Failed to upload asset to Github release. "
            f"(HTTP {response.status}: {await response.text()})"
        )
