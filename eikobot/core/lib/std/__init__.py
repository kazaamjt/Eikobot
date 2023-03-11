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

import asyncssh
from asyncssh.connection import SSHClientConnection as SSHConnection
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
    username: Optional[str] = None
    password: Optional[str] = None
    ssh_requires_pass: bool = False
    sudo_requires_pass: bool = True

    class Config:
        arbitrary_types_allowed = True
        extra = Extra.allow

    def __post_init__(self) -> None:
        self._connection: SSHConnection
        self._con_ref_count: int = 0
        self._connected: asyncio.Event = asyncio.Event()
        self._disconnect_tasks: list[asyncio.Task] = []

    async def _connect(self, ctx: HandlerContext) -> None:
        self._con_ref_count += 1
        if self._con_ref_count == 1:
            ctx.debug(f"SSH: Connecting to '{self.host}'.")
            self._connection = await self._create_connection()
            ctx.debug(f"SSH: Connected to '{self.host}'.")
            self._connected.set()

        else:
            ctx.debug(f"SSH: Reusing existing connection to '{self.host}'.")
            await self._connected.wait()

    async def _create_connection(self) -> SSHConnection:
        extra_args: dict[str, str] = {}
        if self.username is not None:
            extra_args["username"] = self.username

        if self.ssh_requires_pass:
            if self.password is not None:
                extra_args["password"] = self.password

        return await asyncssh.connect(self.host, **extra_args)

    def _set_idle(self, ctx: HandlerContext) -> None:
        self._disconnect_tasks.append(
            asyncio.create_task(
                self._disconnect_delay(ctx),
                name=f"disconnect-{self.host}-{self._con_ref_count}",
            )
        )

    async def _disconnect_delay(self, ctx: HandlerContext) -> None:
        await asyncio.sleep(1)
        self._disconnect(ctx)

    def _disconnect(self, ctx: HandlerContext) -> None:
        self._con_ref_count -= 1
        if self._con_ref_count == 0:
            self._connection.close()
            ctx.debug(f"SSH: Disconnected from '{self.host}'.")

    async def wait_until_disconnected(self) -> None:
        await asyncio.gather(*self._disconnect_tasks)

    async def execute(
        self,
        cmd: str,
        ctx: HandlerContext,
        original_command: Optional[str] = None,
    ) -> CmdResult:
        """
        Execute a command on the remote host.
        Command will not be recorded.
        """
        if original_command is None:
            original_command = cmd
        ctx.debug("Execute: " + original_command)
        cmd_str = 'HISTIGNORE="*" ' + cmd

        await self._connect(ctx)
        process = await self._connection.run(cmd_str, term_type="xterm-color")
        self._set_idle(ctx)

        if process.stdout is None:
            _stdout = ""
        elif isinstance(process.stdout, bytes):
            _stdout = process.stdout.decode()
        else:
            _stdout = process.stdout
        stdout = self._clean_log(_stdout)
        ctx.debug("stdout:\n" + stdout)

        returncode = 1
        if process.returncode is not None:
            returncode = process.returncode

        return CmdResult(original_command, returncode, stdout, "", ctx)

    async def execute_sudo(self, cmd: str, ctx: HandlerContext) -> CmdResult:
        """
        Runs commands that require sudo.
        Sudo still needs to be put in to the commands,
        but you don't have to pass the password yourself.
        """
        if self.sudo_requires_pass and self.password is None:
            return CmdResult(cmd, 1, "", "Sudo password is required, but not set!", ctx)

        if self.sudo_requires_pass:
            return await self.execute(
                f"echo -n {self.password} | sudo -S ls > /dev/null && " + cmd,
                ctx,
                cmd,
            )

        return await self.execute(cmd, ctx)

    def _clean_log(self, log: str) -> str:
        log = log.replace("\r\n", "\n")
        sudo_log_str = "[sudo] password for "
        if self.username is not None:
            sudo_log_str += self.username
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

        result = await ctx.resource.execute("echo $OSTYPE", ctx)
        if result.returncode == 0:
            ctx.deployed = True
        else:
            ctx.failed = True
            return

        os_platform_promis = ctx.resource.raw_resource.promises["os_platform"]
        os_name_promise = ctx.resource.raw_resource.promises["os_name"]
        os_version_promis = ctx.resource.raw_resource.promises["os_version"]

        os_string = result.stdout.replace("\n", "")
        os_platform_promis.set(os_string, ctx)
        if os_string == "":
            os_name_promise.set("windows", ctx)
            os_version_result = await ctx.resource.execute(
                r'(Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion").ReleaseId',
                ctx,
            )
            os_version_promis.set(os_version_result.stdout.replace("\n", ""), ctx)
        elif os_string == "linux-gnu":
            os_release = await ctx.resource.execute("cat /etc/os-release", ctx)
            os_info: dict[str, str] = {}
            for line in os_release.stdout.splitlines():
                key, value = line.split("=")
                os_info[key] = value

            os_name_promise.set(os_info["ID"], ctx)
            os_version_promis.set(os_info["VERSION_ID"], ctx)

        else:
            os_name_promise.set("unknown", ctx)
            os_version_promis.set("unknown", ctx)


@eiko_plugin()
def get_pass(prompt: str = "Password: ") -> EikoProtectedStr:
    return EikoProtectedStr(getpass.getpass(prompt))


class CmdModel(EikoBaseModel):
    """
    A command that will be executed on a remote host.
    """

    __eiko_resource__ = "Cmd"

    host: HostModel
    cmd: str


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
        if result.failed():
            return

        ctx.deployed = True
