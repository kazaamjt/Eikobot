# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
from pathlib import Path

import pytest

from eikobot.core.compiler import Compiler
from eikobot.core.compiler.definitions.base_types import EikoBool
from eikobot.core.compiler.errors import EikoCompilationError


def test_equals(tmp_eiko_file: Path) -> None:
    compiler = Compiler()
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write("a = 3 == 3")

    compiler.compile(tmp_eiko_file)
    a = compiler.context.get("a")
    assert isinstance(a, EikoBool)
    assert a.value

    compiler.reset()
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write("a = 4 == 3")

    compiler.compile(tmp_eiko_file)
    a = compiler.context.get("a")
    assert isinstance(a, EikoBool)
    assert not a.value

    compiler.reset()
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write("a = '3' == '3'")

    compiler.compile(tmp_eiko_file)
    a = compiler.context.get("a")
    assert isinstance(a, EikoBool)
    assert a.value

    compiler.reset()
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write("a = 3 == '3'")

    compiler.compile(tmp_eiko_file)
    a = compiler.context.get("a")
    assert isinstance(a, EikoBool)
    assert not a.value


def test_lt_or_eq(tmp_eiko_file: Path) -> None:
    compiler = Compiler()
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write("a = 3 <= 3")

    compiler.compile(tmp_eiko_file)
    a = compiler.context.get("a")
    assert isinstance(a, EikoBool)
    assert a.value

    compiler.reset()
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write("a = 2 <= 3")

    compiler.compile(tmp_eiko_file)
    a = compiler.context.get("a")
    assert isinstance(a, EikoBool)
    assert a.value

    compiler.reset()
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write("a = 4 <= 3")

    compiler.compile(tmp_eiko_file)
    a = compiler.context.get("a")
    assert isinstance(a, EikoBool)
    assert not a.value

    compiler.reset()
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write("a = 4 <= '3'")

    with pytest.raises(EikoCompilationError):
        compiler.compile(tmp_eiko_file)


def test_gt_or_eq(tmp_eiko_file: Path) -> None:
    compiler = Compiler()
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write("a = 3 >= 3")

    compiler.compile(tmp_eiko_file)
    a = compiler.context.get("a")
    assert isinstance(a, EikoBool)
    assert a.value

    compiler.reset()
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write("a = 2 >= 3")

    compiler.compile(tmp_eiko_file)
    a = compiler.context.get("a")
    assert isinstance(a, EikoBool)
    assert not a.value

    compiler.reset()
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write("a = 4 >= 3")

    compiler.compile(tmp_eiko_file)
    a = compiler.context.get("a")
    assert isinstance(a, EikoBool)
    assert a.value

    compiler.reset()
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write("a = 4 >= '3'")

    with pytest.raises(EikoCompilationError):
        compiler.compile(tmp_eiko_file)


def test_gt_and_lt(tmp_eiko_file: Path) -> None:
    compiler = Compiler()
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write("a = 3 > 3")

    compiler.compile(tmp_eiko_file)
    a = compiler.context.get("a")
    assert isinstance(a, EikoBool)
    assert not a.value

    compiler = Compiler()
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write("a = 3 < 3")

    compiler.compile(tmp_eiko_file)
    a = compiler.context.get("a")
    assert isinstance(a, EikoBool)
    assert not a.value

    compiler = Compiler()
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write("a = 4 > 3")

    compiler.compile(tmp_eiko_file)
    a = compiler.context.get("a")
    assert isinstance(a, EikoBool)
    assert a.value

    compiler = Compiler()
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write("a = 3 < 4")

    compiler.compile(tmp_eiko_file)
    a = compiler.context.get("a")
    assert isinstance(a, EikoBool)
    assert a.value

    compiler.reset()
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write("a = '4' > '3'")

    compiler.compile(tmp_eiko_file)
    a = compiler.context.get("a")
    assert isinstance(a, EikoBool)
    assert a.value
