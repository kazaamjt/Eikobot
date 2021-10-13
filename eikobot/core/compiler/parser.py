from pathlib import Path
from typing import Dict, Iterator, List, Tuple, Union

from . import ast
from .compilation_context import ResourceProperty
from .errors import EikoCompilationError, EikoParserError, EikoSyntaxError
from .lexer import Lexer
from .token import Token, TokenType


class Parser:
    """
    Parses tokens 1 by 1, and turns them in to Expressions.
    """

    def __init__(self, file: Path) -> None:
        self.lexer = Lexer(file)
        self._current = self.lexer.next_token()
        self._next = self.lexer.next_token()
        self._bin_op_precedence = {
            "=": 10,
            "or": 20,
            "and": 30,
            "==": 50,
            "!=": 50,
            "<": 50,
            ">": 50,
            "<=": 50,
            ">=": 50,
            "+": 60,
            "-": 60,
            "*": 70,
            "/": 70,
            "//": 70,
            "%": 70,
            "u-": 80,
            "unot": 40,
            "**": 90,
            ".": 100,
        }

    def parse(self) -> Iterator[ast.ExprAST]:
        """Parses tokens and constructs the next set of ASTs."""
        expr = self._parse_top_level()
        while not isinstance(expr, ast.EOFExprAST):
            yield expr
            expr = self._parse_top_level()

    def print_op_precedence(self) -> None:
        """outputs every level and ops associated with said level."""
        op_precedents: Dict[int, List[str]] = {}
        for key, value in self._bin_op_precedence.items():
            _list = op_precedents.get(value)
            if _list is None:
                _list = []
                op_precedents[value] = _list
            _list.append(key)

        for level, _list in sorted(op_precedents.items()):
            print(f"{level}: [", ", ".join(_list), "]")

    def _advance(self, skip_indentation: bool = False) -> None:
        self._current = self._next
        self._next = self.lexer.next_token()

        if skip_indentation and self._current.type == TokenType.INDENT:
            self._advance(skip_indentation)

        if (
            self._current.type == TokenType.STRING
            and self._next.type == TokenType.STRING
        ):
            self._next = Token(
                TokenType.STRING,
                self._current.content + self._next.content,
                self._current.index,
            )
            self._advance(skip_indentation)

        if (
            self._current.type == TokenType.INDENT
            and self._current.content == ""
            and self._next.type == TokenType.INDENT
        ):
            self._advance()

    def _parse_top_level(self) -> ast.ExprAST:
        if self._current.type != TokenType.INDENT or self._current.content != "":
            raise EikoParserError(
                f"Unexpected token: {self._current.content}.", token=self._current
            )

        self._advance()
        if self._current.type == TokenType.EOF:
            return ast.EOFExprAST(self._current)

        if self._current.type == TokenType.RESOURCE:
            return self._parse_resource_definition()

        return self._parse_expression()

    def _parse_expression(self, precedence: int = 0) -> ast.ExprAST:
        lhs = self._parse_primary()
        return self._parse_bin_op_rhs(precedence, lhs)

    def _parse_primary(self) -> ast.ExprAST:
        if self._current.type == TokenType.INDENT:
            if self._current.content == "":
                self._advance()
                return self._parse_primary()

        if self._current.content in ["-", "not"]:
            return self._parse_unary_op()

        if self._current.type == TokenType.INTEGER:
            token = self._current
            self._advance()
            return ast.IntExprAST(token)

        if self._current.type == TokenType.FLOAT:
            token = self._current
            self._advance()
            return ast.FloatExprAST(token)

        if self._current.type == TokenType.STRING:
            token = self._current
            self._advance()
            return ast.StringExprAST(token)

        if self._current.type == TokenType.LEFT_PAREN:
            return self._parse_parens()

        raise EikoSyntaxError(f"Unexpected token {self._current.type}.")

    def _parse_unary_op(self) -> Union[ast.UnaryNegExprAST, ast.UnaryNotExprAST]:
        token = self._current
        self._advance()
        if token.content == "-":
            rhs = self._parse_expression(self._bin_op_precedence["u-"])
            return ast.UnaryNegExprAST(token, rhs)

        rhs = self._parse_expression(self._bin_op_precedence["unot"])
        return ast.UnaryNotExprAST(token, rhs)

    def _parse_parens(self) -> ast.ExprAST:
        self._advance(skip_indentation=True)
        next_expr = self._parse_expression()
        if self._current.type != TokenType.RIGHT_PAREN:
            raise EikoParserError("Unexpected token.", token=self._current)

        self._advance()
        return next_expr

    def _parse_bin_op_rhs(self, expr_precedence: int, lhs: ast.ExprAST) -> ast.ExprAST:
        while True:
            current_predecedence = self._bin_op_precedence.get(self._current.content, 0)
            if current_predecedence < expr_precedence:
                return lhs
            if self._current.type in [
                TokenType.INDENT,
                TokenType.RIGHT_PAREN,
                TokenType.COMMA,
            ]:
                return lhs

            bin_op_token = self._current
            self._advance()
            rhs = self._parse_primary()

            # if current op binds less tightly with rhs than the operator after rhs,
            # let the pending operator take rhs as it's lhs
            next_op_precedence = self._bin_op_precedence.get(self._current.content, 0)
            if expr_precedence < next_op_precedence:
                rhs = self._parse_bin_op_rhs(current_predecedence + 1, rhs)

            lhs = ast.BinOpExprAST(bin_op_token, lhs, rhs)

    def _parse_resource_definition(self) -> ast.ResourceDefinitionAST:
        if self._next.type != TokenType.IDENTIFIER:
            raise EikoCompilationError(
                f"Unexpected token {self._next.content}, "
                "expected resource identifier.",
                token=self._next,
            )

        rd_ast = ast.ResourceDefinitionAST(self._current, self._next.content)

        self._advance()
        self._advance()

        if self._current.content != ":":
            raise EikoCompilationError(
                f"Unexpected token {self._current.content}.",
                token=self._current,
            )

        self._advance()
        if self._current.type != TokenType.INDENT:
            raise EikoCompilationError(
                f"Unexpected token {self._current.content}, "
                "expected indented code block.",
                token=self._current,
            )

        indent = self._current.content
        while self._current.type == TokenType.INDENT:
            if self._current.content == "":
                break
            if self._current.content != indent:
                raise EikoCompilationError(
                    "Unexpected indentation.",
                    token=self._current,
                )
            self._advance()
            token, prop = self._parse_resource_property()
            rd_ast.add_property(prop, token)

        return rd_ast

    def _parse_resource_property(self) -> Tuple[Token, ResourceProperty]:
        if self._current.type != TokenType.IDENTIFIER:
            raise EikoCompilationError(
                "Unexpected token. Expected a property identifier.",
                token=self._current,
            )

        token = self._current
        name = self._current.content
        default_value = None

        self._advance()
        if self._current.content == ":":
            self._advance()
            if self._current.type != TokenType.IDENTIFIER:
                raise EikoCompilationError(
                    "Unexpected token. Expected a type identifier.",
                    token=self._current,
                )
            prop_type = self._current.content
            self._advance()

        else:
            raise EikoCompilationError(
                "Unexpected token. Expected a type identifier.",
                token=self._current,
            )

        return token, ResourceProperty(name, prop_type, default_value)
