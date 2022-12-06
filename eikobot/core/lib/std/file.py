"""
The file module helps to create and manipulate files.
"""
from pathlib import Path
from typing import Optional, Union

from jinja2 import Template

from eikobot.core.handlers import AsyncCRUDHandler, HandlerContext
from eikobot.core.lib.std import AsyncSSHCmd, HostModel
from eikobot.core.plugin import EikoPluginException, eiko_plugin
from eikobot.core.helpers import EikoBaseModel


@eiko_plugin()
def read_file(path: Path) -> str:
    return path.read_text(encoding="UTF-8")


@eiko_plugin()
def render_template(template: str, data: dict) -> str:
    """
    Takes a jinja template and data as input, and returns a rendered template.
    """
    jinja_template = Template(template)

    _data: dict[str, Union[str, int, bool, float]] = {}
    for key, value in data.items():
        if not isinstance(key, str):
            raise EikoPluginException(
                "render_template requires keys in its data dict to be strings."
            )

        if not isinstance(value, (str, int, bool, float)):
            raise EikoPluginException(
                "render_template requires values to be strings, "
                "bools, floats or integers."
            )

        _data[key] = value

    return jinja_template.render(_data)


class FileModel(EikoBaseModel):
    """
    Represents the eiko 'File' class
    """

    __eiko_resource__ = "File"

    host: HostModel
    path: Path
    content: str
    owner: Optional[str] = None
    group: Optional[str] = None
    mode: int = 664


class FileHandler(AsyncCRUDHandler):
    """Deploys a file on the target machine using ssh."""

    resource = "File"

    async def create(self, ctx: HandlerContext) -> None:
        if not isinstance(ctx.resource, FileModel):
            ctx.failed = True
            return

        result = await AsyncSSHCmd(
            ctx.resource.host, f"mkdir -p {ctx.resource.path.parent}"
        ).execute()
        if result.return_code != 0:
            ctx.failed = True
            return

        result = await AsyncSSHCmd(
            ctx.resource.host, f"echo -n {ctx.resource.content} > {ctx.resource.path}"
        ).execute()
        if result.return_code != 0:
            ctx.failed = True
            return

    async def read(self, ctx: HandlerContext) -> None:
        if not isinstance(ctx.resource, FileModel):
            ctx.failed = True
            return

        result = await AsyncSSHCmd(
            ctx.resource.host, f"cat {ctx.resource.path}"
        ).execute()
        if result.return_code == 0:
            ctx.deployed = True
            if result.stdout.decode() != ctx.resource.content:
                ctx.add_change("content", result.stdout.decode())

    async def update(self, ctx: HandlerContext) -> None:
        if not isinstance(ctx.resource, FileModel):
            ctx.failed = True
            return
