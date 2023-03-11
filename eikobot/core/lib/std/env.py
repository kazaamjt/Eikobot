"""
Interact with the environment on the machine
compiling the code.
"""
import os
from pathlib import Path

from eikobot.core.helpers import EikoProtectedStr
from eikobot.core.plugin import EikoPluginException, eiko_plugin


def _get(name: str) -> str:
    value = os.environ.get(name)
    if value is None:
        raise EikoPluginException(f"Environment variable {name} needs to be set.")

    return value


@eiko_plugin()
def get(name: str) -> str:
    """Gets the value of an environment variable."""
    return _get(name)


@eiko_plugin()
def get_secret(name: str) -> EikoProtectedStr:
    """
    Gets an env variable, but protects it from being show on the commandline.
    """
    return EikoProtectedStr(_get(name))


@eiko_plugin()
def secrets_file(path: Path) -> dict[str, EikoProtectedStr]:
    """
    Reads a file with secrets ('SECRET_NAME=SECRET_VALUE')
    """
    secrets: dict[str, EikoProtectedStr] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f.readlines():
            if line.replace(" ", "") in ["", "\n"]:
                continue

            try:
                if line.endswith("\n"):
                    line = line[:-1]
                name, secret = line.split("=")
                secrets[name.replace(" ", "")] = EikoProtectedStr(secret)
            except Exception as e:
                raise EikoPluginException(
                    f"Failed to read secrets_file '{path}'"
                ) from e

    return secrets
