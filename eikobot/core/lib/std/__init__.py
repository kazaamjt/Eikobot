"""
The Eiko standard library contains various quality of life
plugins and resources.
"""
import asyncio
import getpass
import os
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Optional, Type, Union

from colorama import Fore
from pydantic import Extra

from eikobot.core.handlers import Handler, HandlerContext
from eikobot.core.helpers import EikoBaseModel, EikoBaseType, EikoProtectedStr
from eikobot.core.plugin import eiko_plugin


@eiko_plugin()
def debug_msg(msg: str) -> None:
    """Writes a message to the console."""
    print(Fore.BLUE + "DEBUG_MSG" + Fore.RESET, msg)


@eiko_plugin()
def inspect(obj: EikoBaseType) -> None:
    """Pretty print objects to the console."""
    print("INSPECT " + obj.printable())


@eiko_plugin()
def is_ipv4(addr: str) -> bool:
    return _is_ipaddr(addr, IPv4Address)


@eiko_plugin()
def is_ipv6(addr: str) -> bool:
    return _is_ipaddr(addr, IPv6Address)


def _is_ipaddr(addr: str, ip_type: Union[Type[IPv4Address], Type[IPv6Address]]) -> bool:
    try:
        cast_addr = ip_address(addr)
        if isinstance(cast_addr, ip_type):
            return True

    except ValueError:
        pass

    return False


@dataclass
class CmdResult:
    """The result of a command that was run."""

    cmd: str
    returncode: int
    stdout: str
    stderr: str
    ctx: HandlerContext

    def failed(self) -> bool:
        """
        Logs an error and sets the context to failed
        if the command didn't return 0.
        """
        if self.returncode != 0:
            self.ctx.failed = True
            self.ctx.error("Failed to execute " + f'"{self.cmd}"')
            self.ctx.error(f"log:\n{self.stderr}")
            return True

        return False


class HostModel(EikoBaseModel):
    """
    Respresents a host to which you can deploy a resource.
    Can execute ssh commands.
    """

    __eiko_resource__ = "Host"

    host: str
    port: int = 22
    user_name: Optional[str] = None
    password: Optional[str] = None
    ssh_requires_pass: bool = False
    sudo_requires_pass: bool = True

    class Config:
        arbitrary_types_allowed = True
        extra = Extra.allow

    async def execute(
        self, cmd: str, ctx: HandlerContext, original_command: Optional[str] = None
    ) -> CmdResult:
        """
        Execute a command on the remote host.
        Command will not be recorded.
        """
        if original_command is None:
            original_command = cmd
        ctx.debug("Execute: " + original_command)

        cmd_str = "ssh -t "
        if self.user_name is not None:
            cmd_str += self.user_name
            if self.ssh_requires_pass:
                cmd_str += ":" + str(self.password)
            cmd_str += "@"
        cmd_str += self.host + " '"
        cmd_str += 'HISTIGNORE="*" '
        cmd_str += cmd.replace("'", r"\'")
        cmd_str += "'"

        process = await asyncio.create_subprocess_shell(
            cmd_str,
            stderr=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )

        encoded_stdout, stderr = await process.communicate()
        stdout = self._clean_log(encoded_stdout.decode())
        ctx.debug("stdout:\n" + stdout)

        returncode = 1
        if process.returncode is not None:
            returncode = process.returncode

        return CmdResult(original_command, returncode, stdout, stderr.decode(), ctx)

    async def execute_sudo(self, cmd: str, ctx: HandlerContext) -> CmdResult:
        """
        Runs commands that require sudo.
        Sudo still needs to be put in to the commands,
        but you don't have to pass the password yourself.
        """
        if self.sudo_requires_pass:
            return await self.execute(
                f"echo -n {self.password} | sudo -S ls > /dev/null && " + cmd,
                ctx,
                cmd,
            )

        return await self.execute(cmd, ctx)

    def _clean_log(self, log: str) -> str:
        sudo_log_str = "[sudo] password for "
        if self.user_name is not None:
            sudo_log_str += self.user_name
        else:
            sudo_log_str += os.getlogin()

        sudo_log_str += ": "
        return log.replace(sudo_log_str, "")


class HostHandler(Handler):
    """
    Represents a remote host.
    """

    __eiko_resource__ = "Host"

    async def execute(self, ctx: HandlerContext) -> None:
        if not isinstance(ctx.resource, HostModel):
            ctx.failed = True
            return

        if ctx.resource.password is None:
            if ctx.resource.ssh_requires_pass:
                ctx.error("ssh password is required, but not set!")
                ctx.failed = True
                return

            if ctx.resource.sudo_requires_pass:
                ctx.error("Sudo password is required, but not set!")
                ctx.failed = True
                return

        result = await ctx.resource.execute("whoami; hostname", ctx)
        if result.returncode == 0:
            ctx.deployed = True
        else:
            ctx.failed = True


@eiko_plugin()
def get_pass(prompt: str = "Password: ") -> EikoProtectedStr:
    return EikoProtectedStr(getpass.getpass(prompt))


class CmdModel(EikoBaseModel):
    """
    A command that will be executed on a remote host.
    """

    host: HostModel
    cmd: str

    __eiko_resource__ = "Cmd"


class CmdHandler(Handler):
    """
    Represents a remote host.

    """

    __eiko_resource__ = "Cmd"

    async def execute(self, ctx: HandlerContext) -> None:
        if not isinstance(ctx.resource, CmdModel):
            ctx.failed = True
            return

        if "sudo" in ctx.resource.cmd:
            ssh_exec = ctx.resource.host.execute_sudo
        else:
            ssh_exec = ctx.resource.host.execute

        result = await ssh_exec(ctx.resource.cmd, ctx)
        if result.returncode != 0:
            ctx.failed = True
            return

        ctx.deployed = True
