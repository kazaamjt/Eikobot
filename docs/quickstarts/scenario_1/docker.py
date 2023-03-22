"""
Models for deploying and managing Docker on a remote host.
"""
from pathlib import Path

from eikobot.core.handlers import CRUDHandler, HandlerContext
from eikobot.core.helpers import EikoBaseModel
from eikobot.core.lib.std import HostModel


class DockerHostModel(EikoBaseModel):
    """
    Model that represents a machine that has docker installed
    """

    __eiko_resource__ = "DockerHost"

    host: HostModel
    port: int = 2357


class DockerHostHandler(CRUDHandler):
    """
    Installs docker on a remote host.
    """

    __eiko_resource__ = "DockerHost"

    async def _verify_install(self, ctx: HandlerContext, host: HostModel) -> bool:
        docker_version = await host.execute("sudo docker --version", ctx)
        return docker_version.returncode == 0

    async def _install(self, ctx: HandlerContext, host: HostModel) -> bool:
        """
        Install docker on a remote host.
        """
        script = (Path(__file__).parent / "install.sh").read_text()
        result = await host.script(script, "bash", ctx)
        if result.failed():
            return False

        return await self._verify_install(ctx, host)

    async def create(self, ctx: HandlerContext) -> None:
        if not isinstance(ctx.resource, DockerHostModel):
            ctx.failed = True
            return

        if not await self._install(ctx, ctx.resource.host):
            ctx.failed = True
            return

        ctx.deployed = True

    async def read(self, ctx: HandlerContext) -> None:
        if not isinstance(ctx.resource, DockerHostModel):
            ctx.failed = True
            return

        if not await self._verify_install(ctx, ctx.resource.host):
            return

        ctx.deployed = True
