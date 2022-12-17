"""
The file module helps to create and manipulate files.
"""
from pathlib import Path
from typing import Optional, Union

from jinja2 import Template

from eikobot.core.handlers import AsyncCRUDHandler, HandlerContext
from eikobot.core.helpers import EikoBaseModel
from eikobot.core.lib.std import AsyncSSHCmd, HostModel
from eikobot.core.plugin import EikoPluginException, eiko_plugin


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
    mode: str = "664"


@eiko_plugin()
def parse_rwx_mode(mode: str) -> str:
    """Parses a mode in rw- style and turns it in to an int style."""
    conversion_table = {
        "x": 1,
        "w": 2,
        "r": 4,
    }
    if len(mode) == 10:
        mode = mode[1:]

    if len(mode) != 9:
        raise EikoPluginException

    oct_1 = 0
    for char in mode[0:2]:
        oct_1 += conversion_table.get(char, 0)
    n_mode = str(oct_1)

    oct_2 = 0
    for char in mode[3:5]:
        oct_2 += conversion_table.get(char, 0)
    n_mode += str(oct_2)

    oct_3 = 0
    for char in mode[6:]:
        oct_3 += conversion_table.get(char, 0)
    n_mode += str(oct_3)

    return n_mode


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

        result = await AsyncSSHCmd(
            ctx.resource.host,
            f"chmod {ctx.resource.mode} " f"{ctx.resource.path}",
        ).execute()
        if result.return_code != 0:
            ctx.failed = True
            return

        if ctx.resource.owner is not None:
            result = await AsyncSSHCmd(
                ctx.resource.host, f"chown {ctx.resource.owner} {ctx.resource.path}"
            ).execute()
            if result.return_code != 0:
                ctx.failed = True
                return

        if ctx.resource.group is not None:
            result = await AsyncSSHCmd(
                ctx.resource.host, f"chgrp {ctx.resource.group} {ctx.resource.path}"
            ).execute()
            if result.return_code != 0:
                ctx.failed = True
                return

        ctx.deployed = True

    async def read(self, ctx: HandlerContext) -> None:
        if not isinstance(ctx.resource, FileModel):
            ctx.failed = True
            return

        cat_result = await AsyncSSHCmd(
            ctx.resource.host, f"cat {ctx.resource.path}"
        ).execute()
        if cat_result.return_code == 0:
            ctx.deployed = True
            if cat_result.stdout.decode() != ctx.resource.content:
                ctx.add_change("content", cat_result.stdout.decode())

            ls_result = await AsyncSSHCmd(
                ctx.resource.host, f"ls -l {ctx.resource.path}"
            ).execute()
            if ls_result.return_code == 0:
                ls_parsed = ls_result.stdout.decode().split(" ")
                if parse_rwx_mode(ls_parsed[0]) != ctx.resource.mode:
                    ctx.add_change("mode", parse_rwx_mode(ls_parsed[0]))
                if (
                    ctx.resource.owner is not None
                    and ls_parsed[2] != ctx.resource.owner
                ):
                    ctx.add_change("owner", ls_parsed[2])
                if (
                    ctx.resource.group is not None
                    and ls_parsed[3] != ctx.resource.group
                ):
                    ctx.add_change("group", ls_parsed[3])
            else:
                ctx.deployed = False

    async def update(self, ctx: HandlerContext) -> None:
        if not isinstance(ctx.resource, FileModel):
            ctx.failed = True
            return

        if ctx.changes.get("content") is not None:
            result = await AsyncSSHCmd(
                ctx.resource.host,
                f"echo -n {ctx.resource.content} > {ctx.resource.path}",
            ).execute()
            if result.return_code != 0:
                ctx.failed = True
                return

        if ctx.changes.get("mode") is not None:
            result = await AsyncSSHCmd(
                ctx.resource.host,
                f"chmod {ctx.resource.mode} " f"{ctx.resource.path}",
            ).execute()
            if result.return_code != 0:
                ctx.failed = True
                return

        if ctx.changes.get("owner") is not None:
            result = await AsyncSSHCmd(
                ctx.resource.host, f"chown {ctx.resource.owner} {ctx.resource.path}"
            ).execute()
            if result.return_code != 0:
                ctx.failed = True
                return

        if ctx.changes.get("group") is not None:
            result = await AsyncSSHCmd(
                ctx.resource.host, f"chgrp {ctx.resource.group} {ctx.resource.path}"
            ).execute()
            if result.return_code != 0:
                ctx.failed = True
                return

        ctx.deployed = True
