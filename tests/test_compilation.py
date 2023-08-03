# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
from pathlib import Path

import pytest

from eikobot.core.compiler import Compiler
from eikobot.core.compiler._parser import Parser
from eikobot.core.compiler.definitions._resource import EikoResourceDefinition
from eikobot.core.compiler.definitions.base_types import (
    EikoBool,
    EikoEnumValue,
    EikoInt,
    EikoList,
    EikoNone,
    EikoResource,
    EikoStr,
)
from eikobot.core.compiler.definitions.context import CompilerContext
from eikobot.core.compiler.definitions.typedef import EikoTypeDef
from eikobot.core.errors import EikoCompilationError


def test_basic_ops(eiko_basic_ops_file: Path) -> None:
    parser = Parser(eiko_basic_ops_file)
    ast_list = list(parser.parse())
    context = CompilerContext("__test__", {})

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


def test_custom_constructor(eiko_constructor_file: Path) -> None:
    compiler = Compiler()
    compiler.compile(eiko_constructor_file)

    res_def = compiler.context.get("ConstructorTestResource")
    assert isinstance(res_def, EikoResourceDefinition)

    var_a = compiler.context.get("a")
    assert isinstance(var_a, EikoResource)

    prop_1 = var_a.get("prop_1")
    assert isinstance(prop_1, EikoStr)
    assert prop_1.value == "test"

    prop_2 = var_a.get("prop_2")
    assert isinstance(prop_2, EikoInt)
    assert prop_2.value == 1

    prop_3 = var_a.get("prop_3")
    assert isinstance(prop_3, EikoStr)
    assert prop_3.value == "testtest"


def test_inheritance(eiko_inheritance_file: Path) -> None:
    compiler = Compiler()
    compiler.compile(eiko_inheritance_file)

    var_a = compiler.context.get("a")
    assert isinstance(var_a, EikoResource)
    assert var_a.type.name == "BaseRes"
    assert var_a.to_py() == {
        "prop_1": "a",
        "prop_2": 1,
    }

    var_b = compiler.context.get("b")
    assert isinstance(var_b, EikoResource)
    assert var_b.type.name == "SubRes"
    assert var_b.type.super is not None
    assert var_b.type.super.name == "BaseRes"
    assert var_b.to_py() == {
        "prop_1": "a",
        "prop_2": 1,
        "prop_3": 1,
    }

    var_c = compiler.context.get("c")
    assert isinstance(var_c, EikoResource)
    assert var_c.type.name == "SubSubRes"
    assert var_c.type.super is not None
    assert var_c.type.super.name == "SubRes"
    assert var_c.type.super.super is not None
    assert var_c.type.super.super.name == "BaseRes"
    assert var_c.to_py() == {
        "prop_1": "a",
        "prop_2": 1,
        "prop_3": "a",
        "prop_4": 1,
    }

    var_d = compiler.context.get("d")
    assert isinstance(var_d, EikoResource)
    assert var_d.type.name == "SubResPropOverwite"
    assert var_d.type.super is not None
    assert var_d.type.super.name == "SubRes"
    assert var_d.type.super.super is not None
    assert var_d.type.super.super.name == "BaseRes"
    assert var_d.to_py() == {
        "prop_1": "a",
        "prop_2": 1,
        "prop_3": "a",
    }

    var_e = compiler.context.get("e")
    assert isinstance(var_e, EikoResource)
    assert var_e.type.name == "Test"
    assert var_e.type.super is not None
    assert var_e.type.super.name == "Object"
    assert var_e.to_py() == {
        "prop_1": var_a.to_py(),
    }

    var_f = compiler.context.get("f")
    assert isinstance(var_f, EikoResource)
    assert var_f.type.name == "Test"
    assert var_f.type.super is not None
    assert var_f.type.super.name == "Object"
    assert var_f.to_py() == {
        "prop_1": var_b.to_py(),
    }

    var_g = compiler.context.get("g")
    assert isinstance(var_g, EikoResource)
    assert var_g.type.name == "Test"
    assert var_g.type.super is not None
    assert var_g.type.super.name == "Object"
    assert var_g.to_py() == {
        "prop_1": var_c.to_py(),
    }

    var_h = compiler.context.get("h")
    assert isinstance(var_h, EikoResource)
    assert var_h.type.name == "Test"
    assert var_h.type.super is not None
    assert var_h.type.super.name == "Object"
    assert var_h.to_py() == {
        "prop_1": var_d.to_py(),
    }

    var_i = compiler.context.get("i")
    assert isinstance(var_i, EikoResource)
    assert var_i.type.name == "TripleDotInherit"
    assert var_i.to_py() == {
        "prop_1": "a",
        "prop_2": 1,
    }


def test_enum(eiko_enum_file: Path) -> None:
    compiler = Compiler()
    compiler.compile(eiko_enum_file)

    var_test_1 = compiler.context.get("test_1")
    assert isinstance(var_test_1, EikoResource)
    assert var_test_1.type.name == "TestRes"
    var_test_1_enum_opt_2 = var_test_1.properties.get("prop_1")
    assert isinstance(var_test_1_enum_opt_2, EikoEnumValue)
    assert var_test_1_enum_opt_2.value == "option_2"

    var_test_2 = compiler.context.get("test_2")
    assert isinstance(var_test_2, EikoResource)
    assert var_test_2.type.name == "TestRes"
    var_test_2_enum_opt_1 = var_test_2.properties.get("prop_1")
    assert isinstance(var_test_2_enum_opt_1, EikoEnumValue)
    assert var_test_2_enum_opt_1.value == "option_1"

    var_enum_to_str = compiler.context.get("enum_to_str")
    assert isinstance(var_enum_to_str, EikoStr)
    assert var_enum_to_str.value == "option_3"


@pytest.mark.parametrize(
    "input_str,outcome",
    [
        ('a = 1\nb = type(a) == "int"', True),
        ('a = 1\nb = type(a) == "str"', False),
        ('a = "1"\nb = type(a) == "str"', True),
        ('a = True\nb = type(a) == "bool"', True),
        ('a = [True]\nb = type(a) == "list[bool]"', True),
    ],
)
def test_type_plugin(tmp_eiko_file: Path, input_str: str, outcome: bool) -> None:
    compiler = Compiler()

    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write(input_str)

    compiler.compile(tmp_eiko_file)
    b = compiler.context.get("b")
    assert isinstance(b, EikoBool)
    assert b.value == outcome


def test_for(eiko_for_file: Path) -> None:
    compiler = Compiler()
    compiler.compile(eiko_for_file)

    results_list = compiler.context.get("test_list")
    assert isinstance(results_list, EikoList)

    assert isinstance(results_list.elements[0], EikoStr)
    assert results_list.elements[0].value == "hello"

    assert isinstance(results_list.elements[1], EikoStr)
    assert results_list.elements[1].value == "haha"

    assert isinstance(results_list.elements[2], EikoInt)
    assert results_list.elements[2].value == 12

    assert isinstance(results_list.elements[3], EikoStr)
    assert results_list.elements[3].value == "key_1"

    assert isinstance(results_list.elements[4], EikoInt)
    assert results_list.elements[4].value == 1
