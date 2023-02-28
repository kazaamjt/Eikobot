"""
Models for deploying and managing Docker on a remote host.
"""
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

    async def _verify_install(self, host: HostModel, ctx: HandlerContext) -> bool:
        docker_version = await host.execute_sudo("sudo docker --version", ctx)
        return docker_version.returncode == 0

    async def _install(self, ctx: HandlerContext, host: HostModel) -> bool:
        """
        Install docker on a remote host.
        """
        apt_get_update = await host.execute_sudo("sudo apt-get update", ctx)
        if apt_get_update.failed():
            return False

        pre_req_installs = await host.execute_sudo(
            "sudo apt-get install -y ca-certificates curl gnupg lsb-release",
            ctx,
        )
        if pre_req_installs.failed():
            return False

        keyring_dir = await host.execute_sudo(
            "sudo mkdir -m 0755 -p /etc/apt/keyrings",
            ctx,
        )
        if keyring_dir.failed():
            return False

        gpg = await host.execute_sudo(
            "sudo rm /etc/apt/keyrings/docker.gpg;"
            "curl -fsSL https://download.docker.com/linux/debian/gpg | "
            "sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg",
            ctx,
        )
        if gpg.failed():
            return False

        docker_apt_file = await host.execute_sudo(
            'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] '
            'https://download.docker.com/linux/debian $(lsb_release -cs) stable" | '
            "sudo tee /etc/apt/sources.list.d/docker.list > /dev/null",
            ctx,
        )
        if docker_apt_file.failed():
            return False

        apt_get_update = await host.execute_sudo("sudo apt-get update", ctx)
        if apt_get_update.failed():
            return False

        docker_install = await host.execute_sudo(
            "sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin",
            ctx,
        )
        if docker_install.failed():
            return False

        return await self._verify_install(host, ctx)

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

        if not await self._verify_install(ctx.resource.host, ctx):
            return

        ctx.deployed = True
