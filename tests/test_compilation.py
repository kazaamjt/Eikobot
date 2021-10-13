# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
from pathlib import Path

from eikobot.core.compiler.eiko_types import EikoInt, EikoStr
from eikobot.core.compiler.parser import Parser


def test_basic_ops(eiko_basic_ops_file: Path) -> None:
    parser = Parser(eiko_basic_ops_file)
    ast_list = list(parser.parse())

    result_1 = ast_list[0].compile()
    assert isinstance(result_1, EikoInt)
    assert result_1.value == 6

    result_2 = ast_list[1].compile()
    assert isinstance(result_2, EikoInt)
    assert result_2.value == -14

    result_3 = ast_list[2].compile()
    assert isinstance(result_3, EikoInt)
    assert result_3.value == -13

    result_4 = ast_list[3].compile()
    assert isinstance(result_4, EikoStr)
    assert result_4.value == "string 1 + string 2"

    result_5 = ast_list[4].compile()
    assert isinstance(result_5, EikoInt)
    assert result_5.value == -4

    result_6 = ast_list[5].compile()
    assert isinstance(result_6, EikoStr)
    assert result_6.value == "hahaha"

    result_7 = ast_list[6].compile()
    assert isinstance(result_7, EikoStr)
    assert result_7.value == "auto concat string"
