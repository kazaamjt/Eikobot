# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
from pathlib import Path

from eikobot.core.compiler import Compiler
from eikobot.core.compiler.definitions.base_types import (
    EikoInt,
    EikoResource,
    EikoStr,
)
from eikobot.core.compiler.definitions.context import CompilerContext
from eikobot.core.compiler.parser import Parser


def test_basic_ops(eiko_basic_ops_file: Path) -> None:
    parser = Parser(eiko_basic_ops_file)
    ast_list = list(parser.parse())
    context = CompilerContext("__test__")

    result_1 = ast_list[0].compile(context)
    assert isinstance(result_1, EikoInt)
    assert result_1.value == 6

    result_2 = ast_list[1].compile(context)
    assert isinstance(result_2, EikoInt)
    assert result_2.value == -14

    result_3 = ast_list[2].compile(context)
    assert isinstance(result_3, EikoInt)
    assert result_3.value == -13

    result_4 = ast_list[3].compile(context)
    assert isinstance(result_4, EikoStr)
    assert result_4.value == "string 1 + string 2"

    result_5 = ast_list[4].compile(context)
    assert isinstance(result_5, EikoInt)
    assert result_5.value == -4

    result_6 = ast_list[5].compile(context)
    assert isinstance(result_6, EikoStr)
    assert result_6.value == "hahaha"

    result_7 = ast_list[6].compile(context)
    assert isinstance(result_7, EikoStr)
    assert result_7.value == "auto concat string"


def test_basic_compiler(eiko_file_3: Path) -> None:
    compiler = Compiler()
    compiler.compile(eiko_file_3)
    test_1 = compiler.context.get("test_1")
    assert isinstance(test_1, EikoResource)

    _ip = test_1.properties["ip"]
    assert isinstance(_ip, EikoStr)
    assert _ip.value == "192.168.0.1"

    ip_2 = test_1.properties["ip_2"]
    assert isinstance(ip_2, EikoStr)
    assert ip_2.value == "192.168.1.1"

    ip_1 = compiler.context.get("ip_1")
    assert isinstance(ip_1, EikoStr)
    assert ip_1.value == "192.168.0.1"
