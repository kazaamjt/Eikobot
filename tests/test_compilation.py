# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
from pathlib import Path

import pytest

from eikobot.core.compiler import Compiler
from eikobot.core.compiler.definitions.base_types import (
    EikoInt,
    EikoNone,
    EikoResource,
    EikoStr,
)
from eikobot.core.compiler.definitions.context import CompilerContext
from eikobot.core.compiler.definitions.typedef import EikoTypeDef
from eikobot.core.errors import EikoCompilationError
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


def test_nested_properties(nested_properties_file: Path) -> None:
    compiler = Compiler()
    compiler.compile(nested_properties_file)
    var_b = compiler.context.get("b")
    assert isinstance(var_b, EikoStr)


def test_typedef(eiko_typedef: Path) -> None:
    compiler = Compiler()
    with pytest.raises(EikoCompilationError):
        compiler.compile(eiko_typedef)

    string_alias = compiler.context.get("string_alias")
    assert isinstance(string_alias, EikoTypeDef)

    str_1 = compiler.context.get("str_1")
    assert isinstance(str_1, EikoStr)
    assert str_1.type.name == "string_alias"

    str_2 = compiler.context.get("str_2")
    assert isinstance(str_2, EikoStr)
    assert str_2.type.name == "string_alias"

    ipv4address = compiler.context.get("IPv4Address")
    assert isinstance(ipv4address, EikoTypeDef)

    var_a = compiler.context.get("a")
    assert isinstance(var_a, EikoStr)
    assert var_a.value == "10.0.0.0"

    res_1 = compiler.context.get("res_1")
    assert isinstance(res_1, EikoResource)

    prop_1 = res_1.get("prop_1")
    assert isinstance(prop_1, EikoStr)
    assert prop_1.value == "192.168.0.1"

    net_port = compiler.context.get("net_port")
    assert isinstance(net_port, EikoInt)
    assert net_port.value == 80
    assert net_port.type.name == "WellKnownPort"
    assert net_port.type.super is not None
    assert net_port.type.super.name == "NetworkPort"


def test_resource_compilation(eiko_file_1: Path) -> None:
    compiler = Compiler()
    compiler.compile(eiko_file_1)

    var_test_1 = compiler.context.get("test_1")
    assert isinstance(var_test_1, EikoResource)

    prop_ip = var_test_1.get("ip")
    assert isinstance(prop_ip, EikoStr)
    assert prop_ip.value == "192.168.0.1"

    prop_ip_2 = var_test_1.get("ip_2")
    assert isinstance(prop_ip_2, EikoStr)
    assert prop_ip_2.value == "192.168.1.1"


def test_unions(eiko_union_file: Path) -> None:
    compiler = Compiler()
    with pytest.raises(EikoCompilationError):
        compiler.compile(eiko_union_file)

    var_a = compiler.context.get("a")
    assert isinstance(var_a, EikoStr)

    var_b = compiler.context.get("b")
    assert isinstance(var_b, EikoNone)


def test_forward_declare(tmp_eiko_file: Path) -> None:
    compiler = Compiler()
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write("a: str\n" + 'a = "test_string"')

    compiler.compile(tmp_eiko_file)

    var_a = compiler.context.get("a")
    assert isinstance(var_a, EikoStr)
    assert var_a.value == "test_string"
