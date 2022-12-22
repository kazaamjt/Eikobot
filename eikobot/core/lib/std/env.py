"""
Interact with the environment on the machine
compiling the code.
"""
import os

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
