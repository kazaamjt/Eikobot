# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
from pathlib import Path

from eikobot.core.compiler.parser import Parser
from eikobot.core.compiler.types import EikoInt


def test_basic_math(eiko_basic_math_file: Path) -> None:
    parser = Parser(eiko_basic_math_file)
    ast_list = [x for x in parser.parse()]
    assert len(ast_list) == 3

    result_1 = ast_list[0].compile()
    assert isinstance(result_1, EikoInt)
    assert result_1.value == 6

    result_2 = ast_list[1].compile()
    assert isinstance(result_2, EikoInt)
    assert result_2.value == -14

    result_3 = ast_list[2].compile()
    assert isinstance(result_3, EikoInt)
    assert result_3.value == -13
