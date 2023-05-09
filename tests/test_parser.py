# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
from pathlib import Path

import pytest

from eikobot.core.compiler._parser import (
    AssignmentExprAST,
    BinOP,
    BinOpExprAST,
    CallExprAst,
    EnumExprAst,
    FromImportExprAST,
    FStringExprAST,
    FStringLexer,
    IntExprAST,
    ListExprAST,
    Parser,
    ResourceDefinitionAST,
    ResourcePropertyAST,
    StringExprAST,
    TypedefExprAST,
    TypeExprAST,
    UnaryNegExprAST,
    VariableExprAST,
)
from eikobot.core.compiler._token import Index, Token, TokenType
from eikobot.core.compiler.definitions.context import CompilerContext
from eikobot.core.errors import EikoParserError


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
    assert isinstance(expr_3.rhs.rhs, ListExprAST)
    expr_3_rhs_rhs = expr_3.rhs.rhs.elements[0]
    assert isinstance(expr_3_rhs_rhs, BinOpExprAST)
    assert expr_3_rhs_rhs.bin_op == BinOP.MULTIPLY
    assert isinstance(expr_3_rhs_rhs.rhs, IntExprAST)
    assert expr_3_rhs_rhs.rhs.value == 2
    assert isinstance(expr_3_rhs_rhs.lhs, IntExprAST)
    assert expr_3_rhs_rhs.lhs.value == 7
    assert isinstance(expr_3.lhs, BinOpExprAST)
    assert expr_3.lhs.bin_op == BinOP.EXPONENTIATION
    assert isinstance(expr_3.lhs.rhs, IntExprAST)
    assert expr_3.lhs.rhs.value == 2
    assert isinstance(expr_3.lhs.lhs, ListExprAST)
    expr_3_lhs_lhs = expr_3.lhs.lhs.elements[0]
    assert isinstance(expr_3_lhs_lhs, BinOpExprAST)
    assert expr_3_lhs_lhs.bin_op == BinOP.INT_DIVIDE
    assert isinstance(expr_3_lhs_lhs.lhs, ListExprAST)
    expr_3_lhs_lhs_lhs = expr_3_lhs_lhs.lhs.elements[0]
    assert isinstance(expr_3_lhs_lhs_lhs, BinOpExprAST)
    assert expr_3_lhs_lhs_lhs.bin_op == BinOP.ADD
    assert isinstance(expr_3_lhs_lhs_lhs.rhs, IntExprAST)
    assert expr_3_lhs_lhs_lhs.rhs.value == 2
    assert isinstance(expr_3_lhs_lhs_lhs.lhs, IntExprAST)
    assert expr_3_lhs_lhs_lhs.lhs.value == 1
    assert isinstance(expr_3_lhs_lhs.rhs, UnaryNegExprAST)
    assert isinstance(expr_3_lhs_lhs.rhs.rhs, IntExprAST)
    assert expr_3_lhs_lhs.rhs.rhs.value == 3

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
    assert isinstance(prop_1, ResourcePropertyAST)
    assert prop_1.name == "ip"
    assert isinstance(prop_1.expr, VariableExprAST)
    assert isinstance(prop_1.expr.type_expr, TypeExprAST)

    prop_2 = expr_1.properties["ip_2"]
    assert isinstance(prop_2.expr, VariableExprAST)
    assert isinstance(prop_2.expr.type_expr, TypeExprAST)

    var_1 = next(parse_iter)
    assert isinstance(var_1, AssignmentExprAST)
    assert isinstance(var_1.lhs, VariableExprAST)
    assert var_1.lhs.identifier == "test_1"
    assert isinstance(var_1.rhs, CallExprAst)
    assert var_1.rhs.identifier == "Test"
    assert len(var_1.rhs.args.elements) == 2
    assert isinstance(var_1.rhs.args.elements[0], StringExprAST)
    assert var_1.rhs.args.elements[0].value == "192.168.0.1"
    assert isinstance(var_1.rhs.args.elements[1], StringExprAST)
    assert var_1.rhs.args.elements[1].value == "192.168.1.1"


def test_f_string_lexer() -> None:
    lexer = FStringLexer(
        Token(
            TokenType.F_STRING,
            "This is an f-string test: {3 + 3}",
            Index(0, 0, Path("test_parser.py")),
        )
    )
    token_0 = lexer.next_token()
    assert token_0 == Token(TokenType.INDENT, "", Index(0, 27, lexer.file_path))
    token_1 = lexer.next_token()
    assert token_1 == Token(TokenType.INTEGER, "3", Index(0, 27, lexer.file_path))
    token_2 = lexer.next_token()
    assert token_2 == Token(TokenType.ARITHMETIC_OP, "+", Index(0, 29, lexer.file_path))
    token_3 = lexer.next_token()
    assert token_3 == Token(TokenType.INTEGER, "3", Index(0, 31, lexer.file_path))
    token_4 = lexer.next_token()
    assert token_4 == Token(TokenType.EOF, "EOF", Index(1, 0, lexer.file_path))

    lexer = FStringLexer(
        Token(
            TokenType.F_STRING,
            "This is an f-string test: {3",
            Index(0, 0, Path("test_parser.py")),
        )
    )

    token_0 = lexer.next_token()
    assert token_0 == Token(TokenType.INDENT, "", Index(0, 27, lexer.file_path))
    token_1 = lexer.next_token()
    assert token_1 == Token(TokenType.INTEGER, "3", Index(0, 27, lexer.file_path))

    with pytest.raises(EikoParserError):
        token_2 = lexer.next_token()


def test_f_string_parser(eiko_f_string_file: Path) -> None:
    f_string_expr = FStringExprAST(
        Token(
            TokenType.F_STRING,
            "This is an f-string test: {3 + 3}, {4 + 4}",
            Index(0, 0, eiko_f_string_file),
        )
    )
    expr_1 = f_string_expr.expressions.get("{3 + 3}")
    assert isinstance(expr_1, BinOpExprAST)
    expr_2 = f_string_expr.expressions.get("{3 + 3}")
    assert isinstance(expr_2, BinOpExprAST)

    compiled_f_string = f_string_expr.compile(CompilerContext("f-string-test", {}))
    assert compiled_f_string.value == f"This is an f-string test: {3 + 3}, {4 + 4}"


def test_parse_typedef(eiko_typedef: Path) -> None:
    parser = Parser(eiko_typedef)
    parse_iter = parser.parse()

    expr_1 = next(parse_iter)
    assert isinstance(expr_1, FromImportExprAST)

    expr_2 = next(parse_iter)
    assert isinstance(expr_2, TypedefExprAST)
    assert expr_2.name == "string_alias"
    assert expr_2.super_type_expr.token.content == "str"
    assert expr_2.condition is None

    expr_3 = next(parse_iter)
    assert isinstance(expr_3, TypedefExprAST)
    assert expr_3.name == "IPv4Address"
    assert expr_3.super_type_expr.token.content == "str"
    assert isinstance(expr_3.condition, CallExprAst)


def test_parse_enum(eiko_enum_file: Path) -> None:
    parser = Parser(eiko_enum_file)
    parse_iter = parser.parse()

    expr_1 = next(parse_iter)
    assert isinstance(expr_1, EnumExprAst)

    expr_2 = next(parse_iter)
    assert isinstance(expr_2, ResourceDefinitionAST)
