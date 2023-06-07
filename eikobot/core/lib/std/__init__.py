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
from asyncssh.listener import SSHListener
from colorama import Fore
from pydantic import Extra

from eikobot.core.handlers import Handler, HandlerContext
from eikobot.core.helpers import (
    EikoBaseModel,
    EikoBaseType,
    EikoDeployError,
    EikoPromise,
    EikoProtectedStr,
)
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
    output: str
    ctx: HandlerContext

    def failed(self) -> bool:
        """
        Logs an error and sets the context to failed
        if the command didn't return 0.
        """
        if self.returncode != 0:
            self.ctx.failed = True
            self.ctx.error("Failed to execute " + f'"{self.cmd}"')
            self.ctx.error(f"log:\n{self.output}")
            return True

        return False


class ForwardedPortListener:
    """Represents a forwarded port that needs to be closed."""

    def __init__(
        self, listener: SSHListener, local_port: int, remote_port: int
    ) -> None:
        self.local_port = local_port
        self.remote_port = remote_port
        self.listener = listener
        self.connections = 1


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

    os_platform: EikoPromise[str]
    os_name: EikoPromise[str]
    os_version: EikoPromise[str]

    class Config:
        arbitrary_types_allowed = True
        extra = Extra.allow

    def __post_init__(self) -> None:
        self._connection: SSHConnection
        self._con_ref_count: int = 0
        self._connected: asyncio.Event = asyncio.Event()
        self._disconnect_tasks: list[asyncio.Task] = []
        self._forwarded_ports: dict[int, ForwardedPortListener] = {}
        self._forwarded_ports_stop_tasks: list[asyncio.Task] = []

    async def connect(self, ctx: HandlerContext) -> None:
        """Connects or reuses a existing connection."""
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

    def disconnect(self, ctx: HandlerContext) -> None:
        """Disconnects if nothing else is using the same connection."""
        self._disconnect_tasks.append(
            asyncio.create_task(
                self._disconnect_delay(ctx),
                name=f"disconnect-{self.host}-{self._con_ref_count}",
            )
        )

    async def _disconnect_delay(self, ctx: HandlerContext) -> None:
        await asyncio.sleep(1)
        self._con_ref_count -= 1
        if self._con_ref_count == 0:
            self._connection.close()
            ctx.debug(f"SSH: Disconnected from '{self.host}'.")

    async def wait_until_disconnected(self) -> None:
        await asyncio.gather(*self._forwarded_ports_stop_tasks)
        await asyncio.gather(*self._disconnect_tasks)

    async def script(
        self, script: str, exec_shell: str, ctx: HandlerContext
    ) -> CmdResult:
        """Runs a script on the remote host."""
        if "sudo " in script:
            ssh_exec = self._execute_sudo
        else:
            ssh_exec = self._execute

        _script = f"{exec_shell} << EOF\n{script}\nEOF"
        return await ssh_exec(_script, ctx, script)

    async def execute(self, cmd: str, ctx: HandlerContext) -> CmdResult:
        """Executes one or more commands in an ssh session."""
        if "sudo " in cmd:
            ssh_exec = self._execute_sudo
        else:
            ssh_exec = self._execute

        return await ssh_exec(cmd, ctx)

    async def _execute(
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

        try:
            await self.connect(ctx)
        except OSError:
            return CmdResult(
                original_command, 1, "SSH: Failed to connect to host.", ctx
            )

        process = await self._connection.run(
            cmd_str,
            term_type="xterm-color",
            stderr=asyncssh.STDOUT,
        )
        self.disconnect(ctx)

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

        return CmdResult(original_command, returncode, stdout, ctx)

    async def _execute_sudo(
        self, cmd: str, ctx: HandlerContext, original_command: Optional[str] = None
    ) -> CmdResult:
        if original_command is None:
            original_command = cmd
        if self.sudo_requires_pass and self.password is None:
            return CmdResult(cmd, 1, "Sudo password is required, but not set!", ctx)

        if self.sudo_requires_pass:
            return await self._execute(
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

    async def forward_port(
        self, ctx: HandlerContext, local_port: int, remote_port: int | None = None
    ) -> None:
        """
        Forwards a port using ssh.
        """
        if remote_port is None:
            remote_port = local_port

        forward_port = self._forwarded_ports.get(local_port)
        if forward_port is None:
            await self.connect(ctx)

            listener = await self._connection.forward_local_port(
                "127.0.0.1",
                local_port,
                "127.0.0.1",
                remote_port,
            )
            ctx.debug(
                f"SSH: Forwarding port '{local_port}' to '{self.host}:{remote_port}'."
            )

            self._forwarded_ports[local_port] = ForwardedPortListener(
                listener, local_port, remote_port
            )
        else:
            if forward_port.remote_port != remote_port:
                raise EikoDeployError(
                    "Trying to forward a port from a local port that is already in use."
                )

            ctx.debug(
                f"SSH: Reusing Forwarded port '{local_port}' to '{self.host}:{remote_port}'."
            )
            forward_port.connections += 1

    async def stop_forwarding_port(self, ctx: HandlerContext, local_port: int) -> None:
        """
        Stop forwarding a previously forwarded port.
        """
        forward_port = self._forwarded_ports.get(local_port)
        if forward_port is None or forward_port.connections == 0:
            ctx.warning("Tried to stop forwarding a port that is not being forwarded.")
            return

        self._forwarded_ports_stop_tasks.append(
            asyncio.create_task(
                self._forward_port_stop_delay(ctx, forward_port),
                name=f"forward_port_stop-{self.host}-{forward_port.connections}",
            )
        )

    async def _forward_port_stop_delay(
        self, ctx: HandlerContext, forward_port: ForwardedPortListener
    ) -> None:
        await asyncio.sleep(1)
        forward_port.connections -= 1
        if forward_port.connections == 0:
            forward_port.listener.close()
            await forward_port.listener.wait_closed()
            ctx.debug(
                f"SSH: stopped Forwarding port '{forward_port.local_port}' to '{self.host}:{forward_port.remote_port}'."
            )
            self.disconnect(ctx)


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
        if result.failed():
            return

        os_platform_promis = ctx.resource.raw_resource.promises["os_platform"]
        os_name_promise = ctx.resource.raw_resource.promises["os_name"]
        os_version_promis = ctx.resource.raw_resource.promises["os_version"]

        os_string = result.output.replace("\n", "")
        os_platform_promis.set(os_string, ctx)
        if os_string == "":
            os_platform_promis.set("windows", ctx)
            os_name_promise.set("windows", ctx)
            os_version_result = await ctx.resource.execute(
                r'(Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion").ReleaseId',
                ctx,
            )
            os_version_promis.set(os_version_result.output.replace("\n", ""), ctx)
        elif os_string == "linux-gnu":
            os_release = await ctx.resource.execute("cat /etc/os-release", ctx)
            os_info: dict[str, str] = {}
            for line in os_release.output.splitlines():
                key, value = line.split("=")
                os_info[key] = value

            os_name_promise.set(os_info["ID"], ctx)
            os_version_promis.set(os_info["VERSION_ID"], ctx)

        else:
            os_name_promise.set("unknown", ctx)
            os_version_promis.set("unknown", ctx)

        ctx.deployed = True

    async def cleanup(self, ctx: HandlerContext) -> None:
        ctx.debug("Cleaning up ssh connection.")
        if isinstance(ctx.resource, HostModel):
            await ctx.resource.wait_until_disconnected()


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
    Represents a command executed on remote host.
    """

    __eiko_resource__ = "Cmd"

    async def execute(self, ctx: HandlerContext) -> None:
        if not isinstance(ctx.resource, CmdModel):
            ctx.failed = True
            return

        result = await ctx.resource.host.execute(ctx.resource.cmd, ctx)
        if result.failed():
            return

        ctx.deployed = True


class ScriptModel(EikoBaseModel):
    """
    A command that will be executed on a remote host.
    """

    __eiko_resource__ = "Script"

    host: HostModel
    script: str
    exec_shell: Optional[str] = None


class ScriptHandler(Handler):
    """
    Runs scripts on remote hosts.
    Writes given script to a file and executes said file.
    Then it cleans up the file.
    """

    __eiko_resource__ = "Script"

    async def execute(self, ctx: HandlerContext) -> None:
        if not isinstance(ctx.resource, ScriptModel):
            ctx.failed = True
            return

        if ctx.resource.exec_shell is None:
            platform = ctx.resource.host.os_platform.resolve(str)
            if platform == "linux-gnu":
                exec_shell = "bash"
            elif platform == "windows":
                exec_shell = "powershell"
            else:
                exec_shell = "bash"
        else:
            exec_shell = ctx.resource.exec_shell

        result = await ctx.resource.host.script(ctx.resource.script, exec_shell, ctx)
        if result.failed():
            return

        ctx.deployed = True


@eiko_plugin("hash")
def hash_plugin(string: str) -> str:
    return hex(hash(string))
