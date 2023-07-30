"""
The lexer reads strings/files and turns the characters
in to tokens useable that can be used by the parser
to construct an Abstract Syntax Tree.
"""
from pathlib import Path
from typing import Optional

from ..errors import EikoSyntaxError
from ._token import Token, TokenType
from .misc import Index

KEYWORDS = {
    "resource": TokenType.RESOURCE,
    "implement": TokenType.IMPLEMENT,
    "True": TokenType.TRUE,
    "False": TokenType.FALSE,
    "import": TokenType.IMPORT,
    "typedef": TokenType.TYPEDEF,
    "if": TokenType.IF,
    "elif": TokenType.ELIF,
    "else": TokenType.ELSE,
    "from": TokenType.FROM,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "def": TokenType.DEF,
    "promise": TokenType.PROMISE,
    "enum": TokenType.ENUM,
    "for": TokenType.FOR,
    "in": TokenType.IN,
}

SPECIAL_CHARS = {
    "(": TokenType.LEFT_PAREN,
    ")": TokenType.RIGHT_PAREN,
    "[": TokenType.LEFT_SQ_BRACKET,
    "]": TokenType.RIGHT_SQ_BRACKET,
    "{": TokenType.LEFT_BRACE,
    "}": TokenType.RIGHT_BRACE,
    ",": TokenType.COMMA,
    "@": TokenType.AT_SIGN,
}


class Lexer:
    """The lexer parses a given input and creates a set of tokens from said input."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

        self._char_index = 0
        self._line = 0
        self._col = 0
        self._current_line = 0
        self._index = Index(self._line, self._col, self.file_path)

        with open(self.file_path, "r", encoding="utf-8") as _file:
            self._content = _file.read()

        self._current = ""

    def _current_index(self) -> Index:
        return self._index

    def _next_char(self) -> str:
        """
        Gets the next char from given content.
        Returns EOF when depleted.
        """
        if self._char_index >= len(self._content):
            self._index = Index(self._line + 1, 0, self.file_path)
            return "EOF"

        self._index = Index(self._line, self._col, self.file_path)
        char = self._content[self._char_index]

        self._char_index += 1
        self._col += 1
        if char == "\n":
            self._line += 1
            self._col = 0

        return char

    def _next(self) -> None:
        self._current = self._next_char()

    # NOTE: every return has to be preceded by a call to self._next()
    # pylint: disable=too-many-return-statements,too-many-branches
    def next_token(self) -> Token:
        """
        Returns the next gramatical token.
        """
        if self._current == "":
            self._next()
            return Token(TokenType.INDENT, "", self._current_index())

        if self._current == "\n":
            self._next()
            return self._scan_indent()

        # skip whitespace
        while self._current in ["\t", " "]:
            self._next()

        # skip comments
        if self._current == "#":
            while self._current not in ["\n", "EOF"]:
                self._next()

        if self._current == "EOF":
            return Token(TokenType.EOF, "EOF", self._current_index())

        if self._current.isalpha() or self._current == "_":
            if self._current == "f":
                index = self._current_index()
                self._next()
                if self._current in ['"', "'"]:
                    return self._scan_f_string(index)

                return self._scan_identifier("f", index)

            if self._current == "r":
                index = self._current_index()
                self._next()
                if self._current in ['"', "'"]:
                    return self._scan_raw_string(index)

                return self._scan_identifier("r", index)

            return self._scan_identifier()

        if self._current.isnumeric():
            return self._scan_number()

        if self._current in ['"', "'"]:
            return self._scan_string()

        if self._current != "\n":
            return self._scan_other()

        return self.next_token()

    def _scan_indent(self) -> Token:
        indent_str = ""
        index = self._current_index()
        while self._current in ["\t", " "]:
            indent_str += self._current
            self._next()

        return Token(TokenType.INDENT, indent_str, index)

    def _scan_identifier(
        self, identifier: str = "", index: Optional[Index] = None
    ) -> Token:
        if index is None:
            index = self._current_index()

        while self._current.isalnum() or self._current == "_":
            identifier += self._current
            self._next()
            if self._current == "EOF":
                break

        kw_type = KEYWORDS.get(identifier)
        if kw_type is not None:
            return Token(kw_type, identifier, index)

        return Token(TokenType.IDENTIFIER, identifier, index)

    def _scan_number(self) -> Token:
        number = ""
        is_float = False
        index = self._current_index()
        while self._current.isnumeric() or (self._current == "." and not is_float):
            number += self._current
            if self._current == ".":
                is_float = True
            self._next()

        if is_float:
            return Token(TokenType.FLOAT, number, index)

        return Token(TokenType.INTEGER, number, index)

    def _scan_string(self) -> Token:
        _string = ""
        delimiter = self._current
        index = self._current_index()
        self._next()
        while self._current != delimiter:
            _string += self._current
            self._next()
            if self._current == "\n":
                raise EikoSyntaxError(
                    "EOL while scanning string literal", index=self._current_index()
                )

        self._next()
        try:
            escaped_string = bytes(_string, encoding="utf-8").decode(
                encoding="unicode_escape"
            )
        except UnicodeDecodeError as e:
            raise EikoSyntaxError(str(e), index=index) from e

        return Token(TokenType.STRING, escaped_string, index)

    def _scan_raw_string(self, index: Index) -> Token:
        _string = ""
        delimiter = self._current
        self._next()
        while self._current != delimiter:
            _string += self._current
            self._next()
            if self._current == "\n":
                raise EikoSyntaxError(
                    "EOL while scanning string literal", index=self._current_index()
                )

        self._next()
        return Token(TokenType.STRING, _string, index)

    def _scan_f_string(self, index: Index) -> Token:
        string_token = self._scan_string()
        string_token.index = index
        string_token.type = TokenType.F_STRING
        return string_token

    def _scan_other(self) -> Token:  # pylint: disable=too-many-return-statements
        index = self._current_index()
        if self._current in SPECIAL_CHARS:
            special_char = self._current
            self._next()
            return Token(SPECIAL_CHARS[special_char], special_char, index)

        if self._current == ".":
            self._next()
            if self._current == ".":
                self._next()
                if self._current == ".":
                    self._next()
                    return Token(TokenType.TRIPLE_DOT, "...", index)
                return Token(TokenType.DOUBLE_DOT, "..", index)
            return Token(TokenType.DOT, ".", index)

        if self._current == "=":
            self._next()
            if self._current == "=":
                self._next()
                return Token(TokenType.COMPARISON_OP, "==", index)
            return Token(TokenType.ASSIGNMENT_OP, "=", index)

        if self._current == ":":
            self._next()
            if self._current == ":":
                self._next()
                return Token(TokenType.DOUBLE_COLON, "::", index)

            return Token(TokenType.COLON, ":", index)

        if self._current == "+":
            self._next()
            return Token(TokenType.ARITHMETIC_OP, "+", index)

        if self._current == "-":
            self._next()
            return Token(TokenType.ARITHMETIC_OP, "-", index)

        if self._current == "*":
            self._next()
            if self._current == "*":
                self._next()
                return Token(TokenType.ARITHMETIC_OP, "**", index)

            return Token(TokenType.ARITHMETIC_OP, "*", index)

        if self._current == "/":
            self._next()
            if self._current == "/":
                self._next()
                return Token(TokenType.ARITHMETIC_OP, "//", index)

            return Token(TokenType.ARITHMETIC_OP, "/", index)

        if self._current == "<":
            self._next()
            if self._current == "=":
                self._next()
                return Token(TokenType.COMPARISON_OP, "<=", index)
            return Token(TokenType.COMPARISON_OP, "<", index)

        if self._current == ">":
            self._next()
            if self._current == "=":
                self._next()
                return Token(TokenType.COMPARISON_OP, ">=", index)
            return Token(TokenType.COMPARISON_OP, ">", index)

        if self._current == "!":
            self._next()
            if self._current == "=":
                self._next()
                return Token(TokenType.COMPARISON_OP, "!=", index)
            return Token(TokenType.UNKNOWN, "!", index)

        _current = self._current
        self._next()
        return Token(TokenType.UNKNOWN, _current, index)
