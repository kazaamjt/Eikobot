# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
import pytest
from testing_utils import get_file

from eikobot.core.compiler.parser import Parser, ast


def test_basic_math() -> None:
    _file = get_file("test_basic_math.eiko")
    parser = Parser(_file)
    parse_iter = parser.parse()

    expr_1 = next(parse_iter)
    assert isinstance(expr_1, ast.BinOpExprAST)
    assert expr_1.bin_op == ast.BinOP.ADD
    assert isinstance(expr_1.rhs, ast.IntExprAST)
    assert expr_1.rhs.value == 3
    assert isinstance(expr_1.lhs, ast.BinOpExprAST)
    assert expr_1.lhs.bin_op == ast.BinOP.ADD
    assert isinstance(expr_1.lhs.lhs, ast.IntExprAST)
    assert expr_1.lhs.lhs.value == 1
    assert isinstance(expr_1.lhs.rhs, ast.BinOpExprAST)
    assert expr_1.lhs.rhs.bin_op == ast.BinOP.INT_DIVIDE
    assert isinstance(expr_1.lhs.rhs.lhs, ast.IntExprAST)
    assert expr_1.lhs.rhs.lhs.value == 4
    assert isinstance(expr_1.lhs.rhs.rhs, ast.IntExprAST)
    assert expr_1.lhs.rhs.rhs.value == 2

    expr_2 = next(parse_iter)
    assert isinstance(expr_2, ast.BinOpExprAST)
    assert expr_2.bin_op == ast.BinOP.ADD

    assert isinstance(expr_2.lhs, ast.BinOpExprAST)
    assert expr_2.lhs.bin_op == ast.BinOP.ADD
    assert isinstance(expr_2.lhs.lhs, ast.IntExprAST)
    assert expr_2.lhs.lhs.value == 1
    assert isinstance(expr_2.lhs.rhs, ast.BinOpExprAST)
    assert expr_2.lhs.rhs.bin_op == ast.BinOP.INT_DIVIDE
    assert isinstance(expr_2.lhs.rhs.lhs, ast.IntExprAST)
    assert expr_2.lhs.rhs.lhs.value == 2
    assert isinstance(expr_2.lhs.rhs.rhs, ast.UnaryNegExprAST)
    assert isinstance(expr_2.lhs.rhs.rhs.rhs, ast.BinOpExprAST)
    assert expr_2.lhs.rhs.rhs.rhs.bin_op == ast.BinOP.EXPONENTIATION
    assert isinstance(expr_2.lhs.rhs.rhs.rhs.lhs, ast.IntExprAST)
    assert expr_2.lhs.rhs.rhs.rhs.lhs.value == 3
    assert isinstance(expr_2.lhs.rhs.rhs.rhs.rhs, ast.IntExprAST)
    assert expr_2.lhs.rhs.rhs.rhs.rhs.value == 2

    assert isinstance(expr_2.rhs, ast.BinOpExprAST)
    assert expr_2.rhs.bin_op == ast.BinOP.MULTIPLY
    assert isinstance(expr_2.rhs.lhs, ast.UnaryNegExprAST)
    assert isinstance(expr_2.rhs.lhs.rhs, ast.IntExprAST)
    assert expr_2.rhs.lhs.rhs.value == 7
    assert isinstance(expr_2.rhs.rhs, ast.IntExprAST)
    assert expr_2.rhs.rhs.value == 2

    expr_3 = next(parse_iter)
    assert isinstance(expr_3, ast.BinOpExprAST)
    assert expr_3.bin_op == ast.BinOP.ADD
    assert isinstance(expr_3.rhs, ast.UnaryNegExprAST)
    assert isinstance(expr_3.rhs.rhs, ast.BinOpExprAST)
    assert expr_3.rhs.rhs.bin_op == ast.BinOP.MULTIPLY
    assert isinstance(expr_3.rhs.rhs.rhs, ast.IntExprAST)
    assert expr_3.rhs.rhs.rhs.value == 2
    assert isinstance(expr_3.rhs.rhs.lhs, ast.IntExprAST)
    assert expr_3.rhs.rhs.lhs.value == 7
    assert isinstance(expr_3.lhs, ast.BinOpExprAST)
    assert expr_3.lhs.bin_op == ast.BinOP.EXPONENTIATION
    assert isinstance(expr_3.lhs.rhs, ast.IntExprAST)
    assert expr_3.lhs.rhs.value == 2
    assert isinstance(expr_3.lhs.lhs, ast.BinOpExprAST)
    assert expr_3.lhs.lhs.bin_op == ast.BinOP.INT_DIVIDE
    assert isinstance(expr_3.lhs.lhs.lhs, ast.BinOpExprAST)
    assert expr_3.lhs.lhs.lhs.bin_op == ast.BinOP.ADD
    assert isinstance(expr_3.lhs.lhs.lhs.rhs, ast.IntExprAST)
    assert expr_3.lhs.lhs.lhs.rhs.value == 2
    assert isinstance(expr_3.lhs.lhs.lhs.lhs, ast.IntExprAST)
    assert expr_3.lhs.lhs.lhs.lhs.value == 1
    assert isinstance(expr_3.lhs.lhs.rhs, ast.UnaryNegExprAST)
    assert isinstance(expr_3.lhs.lhs.rhs.rhs, ast.IntExprAST)
    assert expr_3.lhs.lhs.rhs.rhs.value == 3

    with pytest.raises(StopIteration):
        next(parse_iter)
