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

        if ctx.resource.host.is_windows_host:
            await self._create_win(ctx, ctx.resource)

        else:
            await self._create(ctx, ctx.resource)

    async def _create(self, ctx: HandlerContext, resource: FileModel) -> None:
        if resource.requires_sudo:
            sudo = "sudo "
        else:
            sudo = ""

        result = await resource.host.execute(
            f"{sudo}mkdir -p {resource.path.parent}", ctx
        )
        if result.returncode != 0:
            ctx.failed = True
            return

        result = await resource.host.execute(
            f'echo -n "{resource.content}" | {sudo}tee {resource.path}',
            ctx,
        )
        if result.returncode != 0:
            ctx.failed = True
            return

        result = await resource.host.execute(
            f"{sudo}chmod {resource.mode} " f"{resource.path}",
            ctx,
        )
        if result.returncode != 0:
            ctx.failed = True
            return

        if resource.owner is not None:
            result = await resource.host.execute(
                f"{sudo}chown {resource.owner} {resource.path}",
                ctx,
            )
            if result.returncode != 0:
                ctx.failed = True
                return

        if resource.group is not None:
            result = await resource.host.execute(
                f"{sudo}chgrp {resource.group} {resource.path}",
                ctx,
            )
            if result.returncode != 0:
                ctx.failed = True
                return

        ctx.deployed = True

    async def _create_win(self, ctx: HandlerContext, resource: FileModel) -> None:
        result = await resource.host.execute(f"mkdir {resource.path.parent}", ctx)
        if result.returncode != 0:
            ctx.failed = True
            return

        with open(ctx.task_cache / resource.path.name, "w", encoding="utf-8") as f:
            f.write(resource.content)

        await resource.host.scp_to(
            str(ctx.task_cache / resource.path.name),
            ctx,
            str(resource.path),
        )

        ctx.deployed = True

    async def read(self, ctx: HandlerContext) -> None:
        if not isinstance(ctx.resource, FileModel):
            ctx.failed = True
            return

        if ctx.resource.host.is_windows_host:
            await self._read_win(ctx, ctx.resource)

        else:
            await self._read(ctx, ctx.resource)

    async def _read(self, ctx: HandlerContext, resource: FileModel) -> None:
        if resource.requires_sudo:
            sudo = "sudo "
        else:
            sudo = ""

        cat_result = await resource.host.execute(f"{sudo}cat {resource.path}", ctx)
        if cat_result.returncode == 0:
            ctx.deployed = True
            if cat_result.output != resource.content:
                ctx.add_change("content", cat_result.output)

            ls_result = await resource.host.execute(f"{sudo}ls -l {resource.path}", ctx)
            if ls_result.returncode == 0:
                if isinstance(ls_result.output, str):
                    ls_parsed = ls_result.output.split(" ")
                    if parse_rwx_mode(ls_parsed[0]) != resource.mode:
                        ctx.add_change("mode", parse_rwx_mode(ls_parsed[0]))
                    if resource.owner is not None and ls_parsed[2] != resource.owner:
                        ctx.add_change("owner", ls_parsed[2])
                    if resource.group is not None and ls_parsed[3] != resource.group:
                        ctx.add_change("group", ls_parsed[3])
                else:
                    ctx.failed = True

    async def _read_win(self, ctx: HandlerContext, resource: FileModel) -> None:
        cat_result = await resource.host.execute(f"cat {resource.path}", ctx)
        if cat_result.returncode == 0:
            ctx.deployed = True
            if cat_result.output != resource.content:
                ctx.add_change("content", cat_result.output)

    async def update(self, ctx: HandlerContext) -> None:
        if not isinstance(ctx.resource, FileModel):
            ctx.failed = True
            return

        if ctx.resource.host.is_windows_host:
            await self._create_win(ctx, ctx.resource)

        else:
            await self._update(ctx, ctx.resource)

    async def _update(self, ctx: HandlerContext, resource: FileModel) -> None:
        if resource.requires_sudo:
            sudo = "sudo "
        else:
            sudo = ""

        if ctx.changes.get("content") is not None:
            result = await resource.host.execute(
                f'echo -n "{resource.content}" | {sudo}tee {resource.path}',
                ctx,
            )
            if result.failed():
                return

        if ctx.changes.get("mode") is not None:
            result = await resource.host.execute(
                f"{sudo}chmod {resource.mode} " f"{resource.path}",
                ctx,
            )
            if result.failed():
                return

        if ctx.changes.get("owner") is not None:
            result = await resource.host.execute(
                f"{sudo}chown {resource.owner} {resource.path}",
                ctx,
            )
            if result.failed():
                return

        if ctx.changes.get("group") is not None:
            result = await resource.host.execute(
                f"{sudo}chgrp {resource.group} {resource.path}",
                ctx,
            )
            if result.failed():
                return

        ctx.deployed = True
