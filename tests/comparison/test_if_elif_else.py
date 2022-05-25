# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
from pathlib import Path

from eikobot.core.compiler import Compiler
from eikobot.core.compiler.definitions.base_types import EikoInt


def test_if(eiko_if_elif_else_file: Path) -> None:
    compiler = Compiler()
    compiler.context.set("a", EikoInt(1))
    compiler.context.set("b", EikoInt(1))
    compiler.compile(eiko_if_elif_else_file)

    c = compiler.context.get("c")
    assert isinstance(c, EikoInt)
    assert c.value == 1

    d = compiler.context.get("d")
    assert isinstance(d, EikoInt)
    assert d.value == 4


def test_elif_1(eiko_if_elif_else_file: Path) -> None:
    compiler = Compiler()
    compiler.context.set("a", EikoInt(2))
    compiler.context.set("b", EikoInt(1))
    compiler.compile(eiko_if_elif_else_file)

    c = compiler.context.get("c")
    assert isinstance(c, EikoInt)
    assert c.value == 2

    d = compiler.context.get("d")
    assert isinstance(d, EikoInt)
    assert d.value == 4


def test_elif_2(eiko_if_elif_else_file: Path) -> None:
    compiler = Compiler()
    compiler.context.set("a", EikoInt(1))
    compiler.context.set("b", EikoInt(2))
    compiler.compile(eiko_if_elif_else_file)

    c = compiler.context.get("c")
    assert isinstance(c, EikoInt)
    assert c.value == 3

    d = compiler.context.get("d")
    assert isinstance(d, EikoInt)
    assert d.value == 4
