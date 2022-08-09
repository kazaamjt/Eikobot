# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
from pathlib import Path

from eikobot.core.compiler import Compiler
from eikobot.core.compiler.definitions.base_types import (
    EikoBool,
    EikoInt,
    EikoList,
    EikoNone,
    EikoStr,
)


def test_optional(tmp_eiko_file: Path) -> None:
    compiler = Compiler()
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write('a: Optional[str] = "test_string"')

    compiler.compile(tmp_eiko_file)

    var_a = compiler.context.get("a")
    assert isinstance(var_a, EikoStr)
    assert var_a.value == "test_string"

    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write("a: Optional[str] = None")

    compiler.reset()
    compiler.compile(tmp_eiko_file)

    var_a = compiler.context.get("a")
    assert isinstance(var_a, EikoNone)


def test_list(eiko_list_file: Path) -> None:
    compiler = Compiler()
    compiler.compile(eiko_list_file)

    var_test_list = compiler.context.get("test_list")
    assert isinstance(var_test_list, EikoList)
    assert len(var_test_list.elements) == 4

    element_0 = var_test_list.elements[0]
    assert isinstance(element_0, EikoStr)
    assert element_0.value == "string_1"

    element_1 = var_test_list.elements[1]
    assert isinstance(element_1, EikoStr)
    assert element_1.value == "string_2"

    element_2 = var_test_list.elements[2]
    assert isinstance(element_2, EikoInt)
    assert element_2.value == 3

    element_3 = var_test_list.elements[3]
    assert isinstance(element_3, EikoBool)
    assert element_3.value is True

    var_a = compiler.context.get("a")
    assert isinstance(var_a, EikoStr)
    assert var_a.value == "string_2"

    var_b = compiler.context.get("b")
    assert isinstance(var_b, EikoInt)
    assert var_b.value == 3
