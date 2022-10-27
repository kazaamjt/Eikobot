# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
from pathlib import Path

from eikobot.core.compiler import Compiler
from eikobot.core.compiler.definitions.base_types import EikoStr


def test_std_file(eiko_std_file_file: Path) -> None:
    compiler = Compiler()
    compiler.compile(eiko_std_file_file)
    read_result = compiler.context.get("b")
    assert isinstance(read_result, EikoStr)
    assert read_result.value == "Value passed was: {{ value }}"

    template_result = compiler.context.get("c")
    assert isinstance(template_result, EikoStr)
    assert template_result.value == "Value passed was: test_value"
