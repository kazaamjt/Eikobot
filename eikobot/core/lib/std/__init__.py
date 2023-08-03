"""
The Eiko standard library contains various quality of life
plugins and resources.
"""
import asyncio
import getpass
import os
import re
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
        self.is_windows_host: bool = False

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

        try:
            return await asyncssh.connect(self.host, **extra_args)
        except asyncssh.HostKeyNotVerifiable as e:
            key_scan = await asyncio.subprocess.create_subprocess_shell(  # pylint: disable=no-member
                f"ssh {self.host} echo",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            _, stderr = await key_scan.communicate()
            if key_scan.returncode != 0:
                raise EikoDeployError(
                    f"Host verification failed \n{stderr.decode()}"
                ) from e
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

    async def scp_to(
        self,
        file_name: str,
        ctx: HandlerContext,
        destination: str | None = None,
    ) -> None:
        """
        Copies a file from the local host to the remote host
        """
        extra_args: dict[str, str] = {}
        if self.username is not None:
            extra_args["username"] = self.username

        if self.ssh_requires_pass:
            if self.password is not None:
                extra_args["password"] = self.password

        if destination is None:
            destination = file_name

        ctx.debug(f"Copying file '{file_name}' to host.")
        await asyncssh.scp(
            file_name,
            f"{self.host}:{destination}",
            **extra_args,  # type: ignore
        )

    async def scp_from(
        self,
        file_name: str,
        ctx: HandlerContext,
        destination: str | None = None,
    ) -> None:
        """
        Copies a file to the local host from the remote host
        """
        extra_args: dict[str, str] = {}
        if self.username is not None:
            extra_args["username"] = self.username

        if self.ssh_requires_pass:
            if self.password is not None:
                extra_args["password"] = self.password

        if destination is None:
            destination = file_name

        ctx.debug(f"Copying file '{file_name}' from host.")
        await asyncssh.scp(
            f"{self.host}:{file_name}",
            destination,
            **extra_args,  # type: ignore
        )

    async def script(
        self, script: str, exec_shell: str, ctx: HandlerContext
    ) -> CmdResult:
        """Runs a script on the remote host."""
        if self.is_windows_host:
            script_file_name = f"script-{ctx.normalized_task_id()}.ps1"
            with open(ctx.task_cache / script_file_name, "w", encoding="utf-8") as f:
                f.write(script)

            extra_args: dict[str, str] = {}
            if self.username is not None:
                extra_args["username"] = self.username

            if self.ssh_requires_pass:
                if self.password is not None:
                    extra_args["password"] = self.password

            await asyncssh.scp(
                ctx.task_cache / script_file_name,
                f"{self.host}:{script_file_name}",
                **extra_args,  # type: ignore
            )
            result = await self._execute_windows(
                f".\\{script_file_name}",
                ctx,
                script,
            )
            await self._connection.run(
                f"del {script_file_name}",
                term_type="xterm-color",
            )
            return result

        if "sudo " in script:
            ssh_exec = self._execute_sudo
        else:
            ssh_exec = self._execute

        _script = f"{exec_shell} << EOF\n{script}\nEOF"
        return await ssh_exec(_script, ctx, script)

    async def execute(self, cmd: str, ctx: HandlerContext) -> CmdResult:
        """Executes one or more commands in an ssh session."""
        if self.is_windows_host:
            ssh_exec = self._execute_windows
        elif "sudo " in cmd:
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
        )
        self.disconnect(ctx)

        if process.stdout is None:
            _stdout = ""
        elif isinstance(process.stdout, bytes):
            _stdout = process.stdout.decode()
        else:
            _stdout = process.stdout
        stdout = self._clean_log(_stdout)

        # try again as Windows
        if "'HISTIGNORE' is not recognized" in stdout:
            ctx.debug(
                "Potential Windows machine detected, retrying with updated settings."
            )
            self.is_windows_host = True
            await self.execute("Set-ExecutionPolicy RemoteSigned", ctx)
            return await self._execute_windows(cmd, ctx)

        if stdout:
            ctx.debug("stdout:\n" + stdout)
        else:
            ctx.debug("stdout:")

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

    async def _execute_windows(
        self,
        cmd: str,
        ctx: HandlerContext,
        original_command: Optional[str] = None,
    ) -> CmdResult:
        if original_command is None:
            original_command = cmd
        ctx.debug("Execute: " + original_command)

        cmd = cmd.replace('"', '\\"')
        if not cmd.startswith("powershell"):
            cmd_str = f'powershell -NoLogo -NoProfile "{cmd}"'
        else:
            cmd_str = cmd

        rcode_file = f"returncode-{ctx.normalized_task_id()}"
        output_file = f"output-{ctx.normalized_task_id()}"
        cmd_str = f"chcp 65001 & {cmd_str} > {output_file} & "
        cmd_str += f"echo %ERRORLEVEL% > {rcode_file}"

        try:
            await self.connect(ctx)
        except OSError:
            return CmdResult(
                original_command, 1, "SSH: Failed to connect to host.", ctx
            )

        await self._connection.run(
            cmd_str,
            term_type="xterm-color",
        )

        extra_args: dict[str, str] = {}
        if self.username is not None:
            extra_args["username"] = self.username

        if self.ssh_requires_pass:
            if self.password is not None:
                extra_args["password"] = self.password

        await asyncssh.scp(
            f"{self.host}:{rcode_file}",
            ctx.task_cache / rcode_file,
            **extra_args,  # type: ignore
        )
        with open(ctx.task_cache / rcode_file, encoding="utf-8") as f:
            returncode = int(f.read())
        os.remove(ctx.task_cache / rcode_file)

        await self._connection.run(
            f"del {rcode_file}",
            term_type="xterm-color",
        )

        await asyncssh.scp(
            f"{self.host}:{output_file}",
            ctx.task_cache / output_file,
            **extra_args,  # type: ignore
        )
        with open(ctx.task_cache / output_file, encoding="utf-8") as f:
            stdout = self._clean_log(f.read())
        os.remove(ctx.task_cache / output_file)

        await self._connection.run(
            f"del {output_file}",
            term_type="xterm-color",
        )

        if stdout:
            ctx.debug("stdout:\n" + stdout)
        else:
            ctx.debug("stdout:")

        self.disconnect(ctx)

        return CmdResult(original_command, returncode, stdout, ctx)

    def _clean_log(self, log: str) -> str:
        log = log.replace("\r\n", "\n")

        # strip all ansi characters
        ansi_escape = re.compile(
            r"""
                \x1B  # ESC
                (?:   # 7-bit C1 Fe (except CSI)
                    [@-Z\\-_]
                |     # or [ for CSI, followed by a control sequence
                    \[
                    [0-?]*  # Parameter bytes
                    [ -/]*  # Intermediate bytes
                    [@-~]   # Final byte
                )
            """,
            re.VERBOSE,
        )
        log = ansi_escape.sub("", log)

        sudo_log_str = "[sudo] password for "
        if self.username is not None:
            sudo_log_str += self.username
        else:
            sudo_log_str += os.getlogin()
        sudo_log_str += ": "
        log = log.replace(sudo_log_str, "")

        # weird windows stuff
        log = log.replace("0;Administrator: C:\\Windows\\system32\\conhost.exe", "")
        log = log.replace("0;C:\\Windows\\system32\\conhost.exe", "")
        log = log.replace("Active code page: 65001", "")

        # strip beeps, lol
        log = log.replace("\x07", "")

        log = log.removesuffix("\n")

        # Remove any extranious whitespace
        while "\n\n\n" in log:
            log = log.replace("\n\n\n", "\n\n")

        return log

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
        if os_string == "":
            os_platform_promis.set("windows", ctx)
            os_name_promise.set("windows", ctx)
            os_version_result = await ctx.resource.execute(
                "(Get-ComputerInfo).WindowsProductName",
                ctx,
            )
            os_version_promis.set(os_version_result.output.replace("\n", ""), ctx)
            await ctx.resource.execute("Set-ExecutionPolicy RemoteSigned", ctx)
            ctx.debug(f"OS Detection: {os_version_promis.resolve(str)}")
        elif os_string == "linux-gnu":
            os_platform_promis.set("linux-gnu", ctx)
            os_release = await ctx.resource.execute("cat /etc/os-release", ctx)
            os_info: dict[str, str] = {}
            for line in os_release.output.splitlines():
                key, value = line.split("=")
                os_info[key] = value

            os_name_promise.set(os_info["ID"], ctx)
            os_version_promis.set(os_info["VERSION_ID"], ctx)
            ctx.debug(
                "OS Detection: "
                f"{os_platform_promis.resolve(str)}-{os_name_promise.resolve(str)}-{os_version_promis.resolve(str)}"
            )

        else:
            os_platform_promis.set("unknown", ctx)
            os_name_promise.set("unknown", ctx)
            os_version_promis.set("unknown", ctx)

            ctx.debug(
                "OS Detection: "
                f"{os_platform_promis.resolve(str)}-{os_name_promise.resolve(str)}-{os_version_promis.resolve(str)}"
            )

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
                exec_shell = "sh"
        else:
            exec_shell = ctx.resource.exec_shell

        result = await ctx.resource.host.script(ctx.resource.script, exec_shell, ctx)
        if result.failed():
            return

        ctx.deployed = True


@eiko_plugin("hash")
def hash_plugin(string: str) -> str:
    return hex(hash(string))
