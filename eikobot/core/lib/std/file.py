"""
The file module helps to create and manipulate files.
"""
from pathlib import Path
from typing import Optional, Union

from jinja2 import Template

from eikobot.core.handlers import CRUDHandler, HandlerContext
from eikobot.core.helpers import EikoBaseModel
from eikobot.core.lib.std import HostModel
from eikobot.core.plugin import EikoPluginException, eiko_plugin


@eiko_plugin()
def read_file(path: Path) -> str:
    """
    Reads a file on the local machine.
    """
    try:
        _path = path.resolve(strict=True)
    except FileNotFoundError as e:
        raise EikoPluginException(f"Failed to read file '{path}'.") from e
    return _path.read_text(encoding="UTF-8")


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
    requires_sudo: bool = False


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


class FileHandler(CRUDHandler):
    """Deploys a file on the target machine using ssh."""

    __eiko_resource__ = "File"

    async def create(self, ctx: HandlerContext) -> None:
        if not isinstance(ctx.resource, FileModel):
            ctx.failed = True
            return

        if ctx.resource.requires_sudo:
            ssh_exec = ctx.resource.host.execute_sudo
            sudo = "sudo "
        else:
            ssh_exec = ctx.resource.host.execute
            sudo = ""

        result = await ssh_exec(f"{sudo}mkdir -p {ctx.resource.path.parent}", ctx)
        if result.returncode != 0:
            ctx.failed = True
            return

        result = await ssh_exec(
            f'echo -n "{ctx.resource.content}" | {sudo}tee {ctx.resource.path}',
            ctx,
        )
        if result.returncode != 0:
            ctx.failed = True
            return

        result = await ssh_exec(
            f"{sudo}chmod {ctx.resource.mode} " f"{ctx.resource.path}",
            ctx,
        )
        if result.returncode != 0:
            ctx.failed = True
            return

        if ctx.resource.owner is not None:
            result = await ssh_exec(
                f"{sudo}chown {ctx.resource.owner} {ctx.resource.path}",
                ctx,
            )
            if result.returncode != 0:
                ctx.failed = True
                return

        if ctx.resource.group is not None:
            result = await ssh_exec(
                f"{sudo}chgrp {ctx.resource.group} {ctx.resource.path}",
                ctx,
            )
            if result.returncode != 0:
                ctx.failed = True
                return

        ctx.deployed = True

    async def read(self, ctx: HandlerContext) -> None:
        if not isinstance(ctx.resource, FileModel):
            ctx.failed = True
            return

        if ctx.resource.requires_sudo:
            ssh_exec = ctx.resource.host.execute_sudo
            sudo = "sudo "
        else:
            ssh_exec = ctx.resource.host.execute
            sudo = ""

        cat_result = await ssh_exec(f"{sudo}cat {ctx.resource.path}", ctx)
        if cat_result.returncode == 0:
            ctx.deployed = True
            if cat_result.stdout != ctx.resource.content:
                ctx.add_change("content", cat_result.stdout)

            ls_result = await ssh_exec(f"{sudo}ls -l {ctx.resource.path}", ctx)
            if ls_result.returncode == 0:
                if isinstance(ls_result.stdout, str):
                    ls_parsed = ls_result.stdout.split(" ")
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
                    ctx.failed = True

    async def update(self, ctx: HandlerContext) -> None:
        if not isinstance(ctx.resource, FileModel):
            ctx.failed = True
            return

        if ctx.resource.requires_sudo:
            ssh_exec = ctx.resource.host.execute_sudo
            sudo = "sudo "
        else:
            ssh_exec = ctx.resource.host.execute
            sudo = ""

        if ctx.changes.get("content") is not None:
            result = await ssh_exec(
                f'echo -n "{ctx.resource.content}" | {sudo}tee {ctx.resource.path}',
                ctx,
            )
            if result.returncode != 0:
                ctx.failed = True
                return

        if ctx.changes.get("mode") is not None:
            result = await ssh_exec(
                f"{sudo}chmod {ctx.resource.mode} " f"{ctx.resource.path}",
                ctx,
            )
            if result.returncode != 0:
                ctx.failed = True
                return

        if ctx.changes.get("owner") is not None:
            result = await ssh_exec(
                f"{sudo}chown {ctx.resource.owner} {ctx.resource.path}",
                ctx,
            )
            if result.returncode != 0:
                ctx.failed = True
                return

        if ctx.changes.get("group") is not None:
            result = await ssh_exec(
                f"{sudo}chgrp {ctx.resource.group} {ctx.resource.path}",
                ctx,
            )
            if result.returncode != 0:
                ctx.failed = True
                return

        ctx.deployed = True
