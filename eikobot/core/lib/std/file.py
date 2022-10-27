"""
The file module helps to create and manipulate files.
"""
from pathlib import Path
from typing import Union

from jinja2 import Template

from eikobot.core.compiler.definitions.base_types import EikoDict
from eikobot.core.plugin import EikoPluginException, eiko_plugin


@eiko_plugin()
def read_file(path: Path) -> str:
    return path.read_text(encoding="UTF-8")


@eiko_plugin()
def render_template(template: str, data: EikoDict) -> str:
    """
    Takes a jinja template and data as input, and returns a rendered template.
    """
    jinja_template = Template(template)

    _data: dict[str, Union[str, int, bool, float]] = {}
    for key, value in data.elements.items():
        if not isinstance(key, str):
            raise EikoPluginException(
                "render_template requires keys in its data dict to be strings."
            )

        converted_value = value.get_value()
        if not isinstance(converted_value, (str, int, bool, float)):
            raise EikoPluginException(
                "render_template requires values to be strings, "
                "bools, floats or integers."
            )

        _data[key] = converted_value

    return jinja_template.render(_data)
