# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
from pathlib import Path

import pytest

from eikobot.core.compiler.definitions.resource import ResourceProperty
from eikobot.core.compiler.parser import (
    AssignmentAST,
    BinOP,
    BinOpExprAST,
    CallExprAst,
    IntExprAST,
    Parser,
    ResourceDefinitionAST,
    StringExprAST,
    UnaryNegExprAST,
    VariableAST,
)


def test_basic_ops(eiko_basic_ops_file: Path) -> None:
    parser = Parser(eiko_basic_ops_file)
    parse_iter = parser.parse()

    expr_1 = next(parse_iter)
    assert isinstance(expr_1, BinOpExprAST)
    assert expr_1.bin_op == BinOP.ADD
    assert isinstance(expr_1.rhs, IntExprAST)
    assert expr_1.rhs.value == 3
    assert isinstance(expr_1.lhs, BinOpExprAST)
    assert expr_1.lhs.bin_op == BinOP.ADD
    assert isinstance(expr_1.lhs.lhs, IntExprAST)
    assert expr_1.lhs.lhs.value == 1
    assert isinstance(expr_1.lhs.rhs, BinOpExprAST)
    assert expr_1.lhs.rhs.bin_op == BinOP.INT_DIVIDE
    assert isinstance(expr_1.lhs.rhs.lhs, IntExprAST)
    assert expr_1.lhs.rhs.lhs.value == 4
    assert isinstance(expr_1.lhs.rhs.rhs, IntExprAST)
    assert expr_1.lhs.rhs.rhs.value == 2

    expr_2 = next(parse_iter)
    assert isinstance(expr_2, BinOpExprAST)
    assert expr_2.bin_op == BinOP.ADD

    assert isinstance(expr_2.lhs, BinOpExprAST)
    assert expr_2.lhs.bin_op == BinOP.ADD
    assert isinstance(expr_2.lhs.lhs, IntExprAST)
    assert expr_2.lhs.lhs.value == 1
    assert isinstance(expr_2.lhs.rhs, BinOpExprAST)
    assert expr_2.lhs.rhs.bin_op == BinOP.INT_DIVIDE
    assert isinstance(expr_2.lhs.rhs.lhs, IntExprAST)
    assert expr_2.lhs.rhs.lhs.value == 2
    assert isinstance(expr_2.lhs.rhs.rhs, UnaryNegExprAST)
    assert isinstance(expr_2.lhs.rhs.rhs.rhs, BinOpExprAST)
    assert expr_2.lhs.rhs.rhs.rhs.bin_op == BinOP.EXPONENTIATION
    assert isinstance(expr_2.lhs.rhs.rhs.rhs.lhs, IntExprAST)
    assert expr_2.lhs.rhs.rhs.rhs.lhs.value == 3
    assert isinstance(expr_2.lhs.rhs.rhs.rhs.rhs, IntExprAST)
    assert expr_2.lhs.rhs.rhs.rhs.rhs.value == 2

    assert isinstance(expr_2.rhs, BinOpExprAST)
    assert expr_2.rhs.bin_op == BinOP.MULTIPLY
    assert isinstance(expr_2.rhs.lhs, UnaryNegExprAST)
    assert isinstance(expr_2.rhs.lhs.rhs, IntExprAST)
    assert expr_2.rhs.lhs.rhs.value == 7
    assert isinstance(expr_2.rhs.rhs, IntExprAST)
    assert expr_2.rhs.rhs.value == 2

    expr_3 = next(parse_iter)
    assert isinstance(expr_3, BinOpExprAST)
    assert expr_3.bin_op == BinOP.ADD
    assert isinstance(expr_3.rhs, UnaryNegExprAST)
    assert isinstance(expr_3.rhs.rhs, BinOpExprAST)
    assert expr_3.rhs.rhs.bin_op == BinOP.MULTIPLY
    assert isinstance(expr_3.rhs.rhs.rhs, IntExprAST)
    assert expr_3.rhs.rhs.rhs.value == 2
    assert isinstance(expr_3.rhs.rhs.lhs, IntExprAST)
    assert expr_3.rhs.rhs.lhs.value == 7
    assert isinstance(expr_3.lhs, BinOpExprAST)
    assert expr_3.lhs.bin_op == BinOP.EXPONENTIATION
    assert isinstance(expr_3.lhs.rhs, IntExprAST)
    assert expr_3.lhs.rhs.value == 2
    assert isinstance(expr_3.lhs.lhs, BinOpExprAST)
    assert expr_3.lhs.lhs.bin_op == BinOP.INT_DIVIDE
    assert isinstance(expr_3.lhs.lhs.lhs, BinOpExprAST)
    assert expr_3.lhs.lhs.lhs.bin_op == BinOP.ADD
    assert isinstance(expr_3.lhs.lhs.lhs.rhs, IntExprAST)
    assert expr_3.lhs.lhs.lhs.rhs.value == 2
    assert isinstance(expr_3.lhs.lhs.lhs.lhs, IntExprAST)
    assert expr_3.lhs.lhs.lhs.lhs.value == 1
    assert isinstance(expr_3.lhs.lhs.rhs, UnaryNegExprAST)
    assert isinstance(expr_3.lhs.lhs.rhs.rhs, IntExprAST)
    assert expr_3.lhs.lhs.rhs.rhs.value == 3

    expr_4 = next(parse_iter)
    assert isinstance(expr_4, BinOpExprAST)
    assert expr_4.bin_op == BinOP.ADD
    assert isinstance(expr_4.rhs, StringExprAST)
    assert expr_4.rhs.value == "string 2"
    assert isinstance(expr_4.lhs, BinOpExprAST)
    assert expr_4.lhs.bin_op == BinOP.ADD
    assert isinstance(expr_4.lhs.lhs, StringExprAST)
    assert expr_4.lhs.lhs.value == "string 1"
    assert isinstance(expr_4.lhs.rhs, StringExprAST)
    assert expr_4.lhs.rhs.value == " + "

    expr_5 = next(parse_iter)
    assert isinstance(expr_5, BinOpExprAST)
    assert expr_5.bin_op == BinOP.SUBTRACT
    assert isinstance(expr_5.rhs, IntExprAST)
    assert expr_5.rhs.value == 4
    assert isinstance(expr_5.lhs, BinOpExprAST)
    assert expr_5.lhs.bin_op == BinOP.SUBTRACT
    assert isinstance(expr_5.lhs.lhs, IntExprAST)
    assert expr_5.lhs.lhs.value == 4
    assert isinstance(expr_5.lhs.rhs, IntExprAST)
    assert expr_5.lhs.rhs.value == 4

    expr_6 = next(parse_iter)
    assert isinstance(expr_6, BinOpExprAST)
    assert expr_6.bin_op == BinOP.MULTIPLY
    assert isinstance(expr_6.lhs, StringExprAST)
    assert expr_6.lhs.value == "ha"
    assert isinstance(expr_6.rhs, IntExprAST)
    assert expr_6.rhs.value == 3

    expr_7 = next(parse_iter)
    assert isinstance(expr_7, StringExprAST)
    assert expr_7.value == "auto concat string"

    with pytest.raises(StopIteration):
        next(parse_iter)


def test_parse_resource(eiko_file_1: Path) -> None:
    parser = Parser(eiko_file_1)
    parse_iter = parser.parse()

    expr_1 = next(parse_iter)
    assert isinstance(expr_1, ResourceDefinitionAST)
    assert len(expr_1.properties) == 2
    prop_1 = expr_1.properties["ip"]
    assert isinstance(prop_1, ResourceProperty)
    assert prop_1.name == "ip"
    assert prop_1.type == "str"
    prop_2 = expr_1.properties["ip_2"]
    assert isinstance(prop_2, ResourceProperty)
    assert prop_2.name == "ip_2"
    assert prop_2.type == "str"

    var_1 = next(parse_iter)
    assert isinstance(var_1, AssignmentAST)
    assert isinstance(var_1.lhs, VariableAST)
    assert var_1.lhs.identifier == "test_1"
    assert isinstance(var_1.rhs, CallExprAst)
    assert var_1.rhs.identifier == "Test"
    assert len(var_1.rhs.args) == 2
    assert isinstance(var_1.rhs.args[0], StringExprAST)
    assert var_1.rhs.args[0].value == "192.168.0.1"
    assert isinstance(var_1.rhs.args[1], StringExprAST)
    assert var_1.rhs.args[1].value == "192.168.1.1"
