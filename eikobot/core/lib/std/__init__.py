"""
The Eiko standard library contains various quality of life
plugins and resources.
"""
import asyncio
import getpass
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Optional, Type, Union

from colorama import Fore

from eikobot.core.handlers import Handler, HandlerContext
from eikobot.core.helpers import EikoBaseModel, EikoBaseType, EikoProtectedStr
from eikobot.core.plugin import eiko_plugin


@eiko_plugin()
def debug_msg(msg: str) -> None:
    """Writes a message to the console."""
    print(Fore.BLUE + "DEBUG_MSG" + Fore.RESET, msg)


@eiko_plugin()
def inspect(obj: EikoBaseType) -> None:
    """Objects to the console."""
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

    returncode: int
    stdout: str
    stderr: str


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
    sudo_requires_pass: bool = True

    async def execute(self, cmd: str) -> CmdResult:
        """Execute a command on the remote host."""

        cmd_str = "ssh "
        if self.user_name is not None:
            cmd_str += self.user_name
            if self.password:
                cmd_str += ":" + self.password
            cmd_str += "@"
        cmd_str += self.host + " "
        cmd_str += 'HISTIGNORE="*" ' + cmd.replace("'", r"\'")

        process = await asyncio.create_subprocess_shell(
            cmd_str,
            stderr=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        returncode = 1
        if process.returncode is not None:
            returncode = process.returncode

        return CmdResult(returncode, stdout.decode(), stderr.decode())

    async def execute_sudo(self, cmd: str) -> CmdResult:
        """
        Runs commands that require sudo.
        Sudo still needs to be put in to the commands, but no passwords are not needed.
        """
        if self.sudo_requires_pass:
            return await self.execute(
                f"echo -n {self.password} | sudo -S ls > /dev/null;" + cmd
            )

        return await self.execute(cmd)


class HostHandler(Handler):
    """For setting up the ssh session to the host."""

    resource = "Host"

    async def execute(self, ctx: HandlerContext) -> None:
        if isinstance(ctx.resource, HostModel):
            result = await ctx.resource.execute("ls")
            if result.returncode != 0:
                ctx.failed = True


@eiko_plugin()
def get_pass(prompt: str = "Password: ") -> EikoProtectedStr:
    return EikoProtectedStr(getpass.getpass(prompt))
