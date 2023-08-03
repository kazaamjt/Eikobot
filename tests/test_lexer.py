# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
from pathlib import Path

import pytest

from eikobot.core.compiler._token import Token, TokenType
from eikobot.core.compiler.lexer import EikoSyntaxError, Lexer
from eikobot.core.compiler.misc import Index


def test_char_generator(eiko_file_1: Path) -> None:
    """
    Tests Lexer._next_char and Lexer._current_index
    """
    i = 0
    line = 0
    col = 0
    lexer = Lexer(eiko_file_1)
    char = lexer._next_char()
    while True:
        if char == "EOF":
            break

        assert lexer._current_index() == Index(line, col, eiko_file_1)
        assert char == lexer._content[i]
        col += 1
        if char == "\n":
            col = 0
            line += 1

        char = lexer._next_char()
        i += 1


def test_token_generator(eiko_file_2: Path) -> None:
    """Tests Lexer._next_char and Lexer._current_index"""
    lexer = Lexer(eiko_file_2)

    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(0, 0, eiko_file_2))
    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(1, 0, eiko_file_2))
    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(2, 0, eiko_file_2))

    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(3, 0, eiko_file_2))
    assert lexer.next_token() == Token(
        TokenType.RESOURCE, "resource", Index(3, 0, eiko_file_2)
    )
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "Host", Index(3, 9, eiko_file_2)
    )
    assert lexer.next_token() == Token(TokenType.COLON, ":", Index(3, 13, eiko_file_2))

    assert lexer.next_token() == Token(TokenType.INDENT, "\t", Index(4, 0, eiko_file_2))
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "ip", Index(4, 1, eiko_file_2)
    )
    assert lexer.next_token() == Token(TokenType.COLON, ":", Index(4, 3, eiko_file_2))
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "IpAddress", Index(4, 5, eiko_file_2)
    )

    assert lexer.next_token() == Token(TokenType.INDENT, "\t", Index(5, 0, eiko_file_2))
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "ssh_key", Index(5, 1, eiko_file_2)
    )
    assert lexer.next_token() == Token(TokenType.COLON, ":", Index(5, 8, eiko_file_2))
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "str", Index(5, 10, eiko_file_2)
    )

    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(6, 0, eiko_file_2))

    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(7, 0, eiko_file_2))
    assert lexer.next_token() == Token(
        TokenType.RESOURCE, "resource", Index(7, 0, eiko_file_2)
    )
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "Debian", Index(7, 9, eiko_file_2)
    )
    assert lexer.next_token() == Token(
        TokenType.LEFT_PAREN, "(", Index(7, 15, eiko_file_2)
    )
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "Host", Index(7, 16, eiko_file_2)
    )
    assert lexer.next_token() == Token(
        TokenType.RIGHT_PAREN, ")", Index(7, 20, eiko_file_2)
    )
    assert lexer.next_token() == Token(TokenType.COLON, ":", Index(7, 21, eiko_file_2))

    assert lexer.next_token() == Token(TokenType.INDENT, "\t", Index(8, 0, eiko_file_2))
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "version", Index(8, 1, eiko_file_2)
    )
    assert lexer.next_token() == Token(TokenType.COLON, ":", Index(8, 8, eiko_file_2))
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "int", Index(8, 10, eiko_file_2)
    )

    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(9, 0, eiko_file_2))

    assert lexer.next_token() == Token(
        TokenType.INDENT, "\t", Index(10, 0, eiko_file_2)
    )
    assert lexer.next_token() == Token(
        TokenType.IMPLEMENT, "implement", Index(10, 1, eiko_file_2)
    )
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "default", Index(10, 11, eiko_file_2)
    )
    assert lexer.next_token() == Token(
        TokenType.LEFT_PAREN, "(", Index(10, 18, eiko_file_2)
    )
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "self", Index(10, 19, eiko_file_2)
    )
    assert lexer.next_token() == Token(TokenType.COMMA, ",", Index(10, 23, eiko_file_2))
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "version", Index(10, 25, eiko_file_2)
    )
    assert lexer.next_token() == Token(TokenType.COLON, ":", Index(10, 32, eiko_file_2))
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "int", Index(10, 34, eiko_file_2)
    )
    assert lexer.next_token() == Token(
        TokenType.RIGHT_PAREN, ")", Index(10, 37, eiko_file_2)
    )
    assert lexer.next_token() == Token(TokenType.COLON, ":", Index(10, 38, eiko_file_2))

    assert lexer.next_token() == Token(
        TokenType.INDENT, "\t\t", Index(11, 0, eiko_file_2)
    )
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "self", Index(11, 2, eiko_file_2)
    )
    assert lexer.next_token() == Token(TokenType.DOT, ".", Index(11, 6, eiko_file_2))
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "version", Index(11, 7, eiko_file_2)
    )
    assert lexer.next_token() == Token(
        TokenType.ASSIGNMENT_OP, "=", Index(11, 15, eiko_file_2)
    )
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "version", Index(11, 17, eiko_file_2)
    )

    assert lexer.next_token() == Token(
        TokenType.INDENT, "\t\t", Index(12, 0, eiko_file_2)
    )
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "self", Index(12, 2, eiko_file_2)
    )
    assert lexer.next_token() == Token(TokenType.DOT, ".", Index(12, 6, eiko_file_2))
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "software", Index(12, 7, eiko_file_2)
    )
    assert lexer.next_token() == Token(
        TokenType.ASSIGNMENT_OP, "=", Index(12, 16, eiko_file_2)
    )
    assert lexer.next_token() == Token(
        TokenType.STRING, "nginx", Index(12, 18, eiko_file_2)
    )

    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(13, 0, eiko_file_2))

    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(14, 0, eiko_file_2))
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "debian_host", Index(14, 0, eiko_file_2)
    )
    assert lexer.next_token() == Token(
        TokenType.ASSIGNMENT_OP, "=", Index(14, 12, eiko_file_2)
    )
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "Debian", Index(14, 14, eiko_file_2)
    )
    assert lexer.next_token() == Token(
        TokenType.LEFT_PAREN, "(", Index(14, 20, eiko_file_2)
    )
    assert lexer.next_token() == Token(
        TokenType.INTEGER, "11", Index(14, 21, eiko_file_2)
    )
    assert lexer.next_token() == Token(
        TokenType.RIGHT_PAREN, ")", Index(14, 23, eiko_file_2)
    )

    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(16, 0, eiko_file_2))

    assert lexer.next_token() == Token(TokenType.EOF, "EOF", Index(16, 0, eiko_file_2))
    # Lexer keeps returning EOF instead of an error. This is by design.
    assert lexer.next_token() == Token(TokenType.EOF, "EOF", Index(16, 0, eiko_file_2))


def test_base_types(eiko_base_type_file: Path) -> None:
    lexer = Lexer(eiko_base_type_file)
    assert lexer.next_token() == Token(
        TokenType.INDENT, "", Index(0, 0, eiko_base_type_file)
    )
    assert lexer.next_token() == Token(
        TokenType.STRING,
        "This test shows off escape \\ sequence parsing.\n",
        Index(0, 0, eiko_base_type_file),
    )

    assert lexer.next_token() == Token(
        TokenType.INDENT, "", Index(1, 0, eiko_base_type_file)
    )
    assert lexer.next_token() == Token(
        TokenType.INTEGER, "123456", Index(1, 0, eiko_base_type_file)
    )

    assert lexer.next_token() == Token(
        TokenType.INDENT, "", Index(2, 0, eiko_base_type_file)
    )
    assert lexer.next_token() == Token(
        TokenType.FLOAT, "123.123", Index(2, 0, eiko_base_type_file)
    )

    assert lexer.next_token() == Token(
        TokenType.INDENT, "", Index(3, 0, eiko_base_type_file)
    )
    assert lexer.next_token() == Token(
        TokenType.STRING, "base string", Index(3, 0, eiko_base_type_file)
    )

    assert lexer.next_token() == Token(
        TokenType.INDENT, "", Index(4, 0, eiko_base_type_file)
    )
    assert lexer.next_token() == Token(
        TokenType.STRING, r"\n\n", Index(4, 0, eiko_base_type_file)
    )

    assert lexer.next_token() == Token(
        TokenType.INDENT, "", Index(5, 0, eiko_base_type_file)
    )
    assert lexer.next_token() == Token(
        TokenType.F_STRING, "Hello, {name}", Index(5, 0, eiko_base_type_file)
    )

    assert lexer.next_token() == Token(
        TokenType.INDENT, "", Index(7, 0, eiko_base_type_file)
    )
    assert lexer.next_token() == Token(
        TokenType.EOF, "EOF", Index(7, 0, eiko_base_type_file)
    )


def test_basic_math(eiko_basic_ops_file: Path) -> None:
    lexer = Lexer(eiko_basic_ops_file)

    assert lexer.next_token() == Token(
        TokenType.INDENT, "", Index(0, 0, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.INTEGER, "1", Index(0, 0, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "+", Index(0, 2, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.INTEGER, "4", Index(0, 4, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "//", Index(0, 6, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.INTEGER, "2", Index(0, 9, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "+", Index(0, 11, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.INTEGER, "3", Index(0, 13, eiko_basic_ops_file)
    )

    assert lexer.next_token() == Token(
        TokenType.INDENT, "", Index(1, 0, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.INTEGER, "1", Index(1, 0, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "+", Index(1, 2, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.INTEGER, "2", Index(1, 4, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "//", Index(1, 6, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "-", Index(1, 9, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.INTEGER, "3", Index(1, 10, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "**", Index(1, 11, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.INTEGER, "2", Index(1, 13, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "+", Index(1, 15, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "-", Index(1, 17, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.INTEGER, "7", Index(1, 18, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "*", Index(1, 20, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.INTEGER, "2", Index(1, 22, eiko_basic_ops_file)
    )

    assert lexer.next_token() == Token(
        TokenType.INDENT, "", Index(2, 0, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.LEFT_PAREN, "(", Index(2, 0, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.LEFT_PAREN, "(", Index(2, 1, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.INTEGER, "1", Index(2, 2, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "+", Index(2, 4, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.INTEGER, "2", Index(2, 6, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.RIGHT_PAREN, ")", Index(2, 7, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "//", Index(2, 9, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "-", Index(2, 12, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.INTEGER, "3", Index(2, 13, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.RIGHT_PAREN, ")", Index(2, 14, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "**", Index(2, 15, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.INTEGER, "2", Index(2, 17, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "+", Index(2, 19, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "-", Index(2, 21, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.LEFT_PAREN, "(", Index(2, 22, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.INTEGER, "7", Index(2, 23, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "*", Index(2, 25, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.INTEGER, "2", Index(2, 27, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.RIGHT_PAREN, ")", Index(2, 28, eiko_basic_ops_file)
    )

    assert lexer.next_token() == Token(
        TokenType.INDENT, "", Index(3, 0, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.STRING, "string 1", Index(3, 0, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "+", Index(3, 11, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.STRING, " + ", Index(3, 13, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "+", Index(3, 19, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.STRING, "string 2", Index(3, 21, eiko_basic_ops_file)
    )

    assert lexer.next_token() == Token(
        TokenType.INDENT, "", Index(4, 0, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.INTEGER, "4", Index(4, 0, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "-", Index(4, 2, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.INTEGER, "4", Index(4, 4, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "-", Index(4, 6, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.INTEGER, "4", Index(4, 8, eiko_basic_ops_file)
    )

    assert lexer.next_token() == Token(
        TokenType.INDENT, "", Index(5, 0, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.STRING, "ha", Index(5, 0, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "*", Index(5, 5, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.INTEGER, "3", Index(5, 7, eiko_basic_ops_file)
    )

    assert lexer.next_token() == Token(
        TokenType.INDENT, "", Index(6, 0, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.STRING, "auto", Index(6, 0, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.STRING, " concat", Index(6, 6, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.STRING, " string", Index(6, 15, eiko_basic_ops_file)
    )

    assert lexer.next_token() == Token(
        TokenType.INDENT, "", Index(8, 0, eiko_basic_ops_file)
    )
    assert lexer.next_token() == Token(
        TokenType.EOF, "EOF", Index(8, 0, eiko_basic_ops_file)
    )


def test_comment_end_of_file_lexing(tmp_eiko_file: Path) -> None:
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write("# Test comment")

    lexer = Lexer(tmp_eiko_file)
    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(0, 0, tmp_eiko_file))
    assert lexer.next_token() == Token(TokenType.EOF, "EOF", Index(1, 0, tmp_eiko_file))


def test_unicode_escape_error(tmp_eiko_file: Path) -> None:
    file_path = "\\U"
    model = f'path = Path("{file_path}")'
    with open(tmp_eiko_file, "w", encoding="utf-8") as f:
        f.write(model)

    lexer = Lexer(tmp_eiko_file)
    lexer.next_token()
    lexer.next_token()
    lexer.next_token()
    lexer.next_token()
    lexer.next_token()
    with pytest.raises(EikoSyntaxError):
        lexer.next_token()
