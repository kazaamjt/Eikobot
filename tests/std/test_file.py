# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
import os
from pathlib import Path

import pytest

from eikobot.core.compiler import Compiler
from eikobot.core.compiler.definitions.base_types import EikoStr
from eikobot.core.deployer import Deployer


def test_std_file(eiko_std_file_file: Path) -> None:
    compiler = Compiler()
    compiler.compile(eiko_std_file_file)
    read_result = compiler.context.get("b")
    assert isinstance(read_result, EikoStr)
    assert read_result.value == "Value passed was: {{ value }}"

    template_result = compiler.context.get("c")
    assert isinstance(template_result, EikoStr)
    assert template_result.value == "Value passed was: test_value"


@pytest.mark.asyncio
async def test_std_file_deploy(tmp_eiko_file: Path) -> None:
    file_path = tmp_eiko_file.parent / "test_std_file_deploy"
    file_content = "It worked!"
    model = f"""
from std import Host
from std.file import File

File(
    host=Host("127.0.0.1"),
    path=Path("{file_path}"),
    content="{file_content}",
)
"""
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write(model)

    deployer = Deployer()
    await deployer.deploy_from_file(tmp_eiko_file)

    assert file_path.exists()
    assert file_path.read_text() == file_content
    assert (oct(os.stat(file_path).st_mode & 0o777))[2:] == "664"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("wrong content")

    await deployer.deploy_from_file(tmp_eiko_file)
    assert file_path.read_text() == file_content
