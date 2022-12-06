"""
The Eiko standard library contains various quality of life
plugins and resources.
"""
import asyncio
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Optional, Type, Union

from colorama import Fore

from eikobot.core.helpers import EikoBaseModel, EikoBaseType
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


class HostModel(EikoBaseModel):
    """Respresents a host to which you can deploy a resource."""

    __eiko_resource__ = "Host"

    target: str
    user_name: Optional[str] = None
    password: Optional[str] = None


@dataclass
class CmdResult:
    """The result of a command that was run."""

    return_code: Optional[int]
    stdout: bytes
    stderr: bytes


@dataclass
class AsyncSSHCmd:
    """Executes a single SSH command."""

    host: HostModel
    cmd: str

    async def execute(self) -> CmdResult:
        """Run the command."""

        cmd_str = "ssh "
        if self.host.user_name is not None:
            cmd_str += self.host.user_name
            if self.host.password:
                cmd_str += ":" + self.host.password
            cmd_str += "@"
        cmd_str += self.host.target + " "
        cmd_str += "'" + self.cmd.replace("'", r"\'") + "'"

        process = await asyncio.create_subprocess_shell(
            cmd_str,
            stderr=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        return CmdResult(process.returncode, stdout, stderr)
