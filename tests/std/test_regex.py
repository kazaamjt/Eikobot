# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
from pathlib import Path

from eikobot.core.compiler import Compiler
from eikobot.core.compiler.definitions.base_types import EikoBool


def test_regex_match(eiko_std_regex_match: Path) -> None:
    compiler = Compiler()
    compiler.compile(eiko_std_regex_match)
    val_1 = compiler.context.get("val_1")
    assert isinstance(val_1, EikoBool)
    assert val_1.value is True
    val_2 = compiler.context.get("val_2")
    assert isinstance(val_2, EikoBool)
    assert val_2.value is False
