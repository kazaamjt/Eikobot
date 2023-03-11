# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
from pathlib import Path

import pytest

from eikobot.core.compiler import Compiler
from eikobot.core.compiler.definitions.base_types import EikoStr
from eikobot.core.deployer import Deployer
from eikobot.core.errors import EikoCompilationError


def test_std_ipaddr(eiko_std_ipaddr: Path) -> None:
    compiler = Compiler()
    compiler.compile(eiko_std_ipaddr)

    a = compiler.context.get("a")
    assert isinstance(a, EikoStr)
    assert a.value == "10.10.10.10"

    b = compiler.context.get("b")
    assert isinstance(b, EikoStr)
    assert b.value == "192.168.1.20"

    c = compiler.context.get("c")
    assert isinstance(c, EikoStr)
    assert c.value == "2001:0db8:75a2:0000:0000:8a2e:0340:5625"

    d = compiler.context.get("d")
    assert isinstance(d, EikoStr)
    assert d.value == "2001:0db8:75a2::8a2e:0340:5626"


@pytest.mark.parametrize(
    "param_input", [("10.10.10.01"), ("10.10.10.300"), ("10.300.10.1")]
)
def test_bad_v4_addr(tmp_eiko_file: Path, param_input: str) -> None:
    with open(tmp_eiko_file, "w", encoding="utf-8") as file:
        content = "from std import IPv4Address\n"
        content = f"IPv4Address('{param_input}')"
        file.write(content)

    with pytest.raises(EikoCompilationError):
        Compiler().compile(tmp_eiko_file)


@pytest.mark.parametrize("param_input", [("2001:0db8:75a2::8a2e::5626")])
def test_bad_v6_addr(tmp_eiko_file: Path, param_input: str) -> None:
    with open(tmp_eiko_file, "w", encoding="utf-8") as file:
        content = "from std import IPv6Address\n"
        content = f"IPv6Address('{param_input}')"
        file.write(content)

    with pytest.raises(EikoCompilationError):
        Compiler().compile(tmp_eiko_file)


@pytest.mark.asyncio
async def test_cmd_deploy(tmp_eiko_file: Path) -> None:
    file_path = tmp_eiko_file.parent / "test_std_file_deploy"
    model = f"""
from std import Host, Cmd

Cmd(
    Host("127.0.0.1"),
    "touch /{file_path}",
)
"""
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write(model)

    deployer = Deployer()
    await deployer.deploy_from_file(tmp_eiko_file)

    assert file_path.exists()
