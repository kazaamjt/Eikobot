"""
Interact with the environment on the machine
compiling the code.
"""
import os

from eikobot.core.plugin import EikoPluginException, eiko_plugin


@eiko_plugin()
def get(name: str) -> str:
    """Gets the value of an environment variable."""
    value = os.environ.get(name)
    if value is None:
        raise EikoPluginException(f"Environment variable {name} needs to be set.")

    return value
