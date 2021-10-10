# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
from pathlib import Path

from eikobot.core.compiler.lexer import Lexer
from eikobot.core.compiler.lexer.token import Token, TokenType
from eikobot.core.compiler.misc import Index


def get_file(name: str) -> Path:
    return Path(__file__).resolve().parent / "files" / name


def test_char_generator() -> None:
    """
    Tests Lexer._next_char and Lexer._current_index
    """
    i = 0
    line = 0
    col = 0
    _file = get_file("test_1.eiko")
    lexer = Lexer(_file)
    char = lexer._next_char()
    while True:
        if char == "EOF":
            break

        assert lexer._current_index() == Index(line, col, _file)
        assert char == lexer._content[i]
        col += 1
        if char == "\n":
            col = 0
            line += 1

        char = lexer._next_char()
        i += 1


def test_token_generator() -> None:
    """Tests Lexer._next_char and Lexer._current_index"""
    _file = get_file("test_2.eiko")
    lexer = Lexer(_file)

    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(0, 0, _file))
    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(1, 0, _file))
    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(2, 0, _file))

    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(3, 0, _file))
    assert lexer.next_token() == Token(
        TokenType.RESOURCE, "resource", Index(3, 0, _file)
    )
    assert lexer.next_token() == Token(TokenType.IDENTIFIER, "Host", Index(3, 9, _file))
    assert lexer.next_token() == Token(TokenType.COLON, ":", Index(3, 13, _file))

    assert lexer.next_token() == Token(TokenType.INDENT, "\t", Index(4, 0, _file))
    assert lexer.next_token() == Token(TokenType.IDENTIFIER, "ip", Index(4, 1, _file))
    assert lexer.next_token() == Token(TokenType.COLON, ":", Index(4, 3, _file))
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "IpAddress", Index(4, 5, _file)
    )

    assert lexer.next_token() == Token(TokenType.INDENT, "\t", Index(5, 0, _file))
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "ssh_key", Index(5, 1, _file)
    )
    assert lexer.next_token() == Token(TokenType.COLON, ":", Index(5, 8, _file))
    assert lexer.next_token() == Token(TokenType.IDENTIFIER, "str", Index(5, 10, _file))

    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(6, 0, _file))

    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(7, 0, _file))
    assert lexer.next_token() == Token(
        TokenType.RESOURCE, "resource", Index(7, 0, _file)
    )
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "Debian", Index(7, 9, _file)
    )
    assert lexer.next_token() == Token(TokenType.LEFT_PAREN, "(", Index(7, 15, _file))
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "Host", Index(7, 16, _file)
    )
    assert lexer.next_token() == Token(TokenType.RIGHT_PAREN, ")", Index(7, 20, _file))
    assert lexer.next_token() == Token(TokenType.COLON, ":", Index(7, 21, _file))

    assert lexer.next_token() == Token(TokenType.INDENT, "\t", Index(8, 0, _file))
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "version", Index(8, 1, _file)
    )
    assert lexer.next_token() == Token(TokenType.COLON, ":", Index(8, 8, _file))
    assert lexer.next_token() == Token(TokenType.IDENTIFIER, "int", Index(8, 10, _file))

    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(9, 0, _file))

    assert lexer.next_token() == Token(TokenType.INDENT, "\t", Index(10, 0, _file))
    assert lexer.next_token() == Token(
        TokenType.IMPLEMENT, "implement", Index(10, 1, _file)
    )
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "default", Index(10, 11, _file)
    )
    assert lexer.next_token() == Token(TokenType.LEFT_PAREN, "(", Index(10, 18, _file))
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "self", Index(10, 19, _file)
    )
    assert lexer.next_token() == Token(TokenType.COMMA, ",", Index(10, 23, _file))
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "version", Index(10, 25, _file)
    )
    assert lexer.next_token() == Token(TokenType.COLON, ":", Index(10, 32, _file))
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "int", Index(10, 34, _file)
    )
    assert lexer.next_token() == Token(TokenType.RIGHT_PAREN, ")", Index(10, 37, _file))
    assert lexer.next_token() == Token(TokenType.COLON, ":", Index(10, 38, _file))

    assert lexer.next_token() == Token(TokenType.INDENT, "\t\t", Index(11, 0, _file))
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "self", Index(11, 2, _file)
    )
    assert lexer.next_token() == Token(TokenType.DOT, ".", Index(11, 6, _file))
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "version", Index(11, 7, _file)
    )
    assert lexer.next_token() == Token(
        TokenType.ASSIGNMENT_OP, "=", Index(11, 15, _file)
    )
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "version", Index(11, 17, _file)
    )

    assert lexer.next_token() == Token(TokenType.INDENT, "\t\t", Index(12, 0, _file))
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "self", Index(12, 2, _file)
    )
    assert lexer.next_token() == Token(TokenType.DOT, ".", Index(12, 6, _file))
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "software", Index(12, 7, _file)
    )
    assert lexer.next_token() == Token(
        TokenType.ASSIGNMENT_OP, "=", Index(12, 16, _file)
    )
    assert lexer.next_token() == Token(TokenType.STRING, "nginx", Index(12, 18, _file))

    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(13, 0, _file))

    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(14, 0, _file))
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "debian_host", Index(14, 0, _file)
    )
    assert lexer.next_token() == Token(
        TokenType.ASSIGNMENT_OP, "=", Index(14, 12, _file)
    )
    assert lexer.next_token() == Token(
        TokenType.IDENTIFIER, "Debian", Index(14, 14, _file)
    )
    assert lexer.next_token() == Token(TokenType.LEFT_PAREN, "(", Index(14, 20, _file))
    assert lexer.next_token() == Token(TokenType.INTEGER, "11", Index(14, 21, _file))
    assert lexer.next_token() == Token(TokenType.RIGHT_PAREN, ")", Index(14, 23, _file))

    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(16, 0, _file))

    assert lexer.next_token() == Token(TokenType.EOF, "EOF", Index(16, 0, _file))
    # Lexer keeps returning EOF instead of an error. This is by design.
    assert lexer.next_token() == Token(TokenType.EOF, "EOF", Index(16, 0, _file))


def test_base_types() -> None:
    _file = get_file("test_base_types.eiko")
    lexer = Lexer(_file)
    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(0, 0, _file))
    assert lexer.next_token() == Token(
        TokenType.STRING,
        "This test shows off escape \\ sequence parsing.\n",
        Index(0, 0, _file),
    )

    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(1, 0, _file))
    assert lexer.next_token() == Token(TokenType.INTEGER, "123456", Index(1, 0, _file))

    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(2, 0, _file))
    assert lexer.next_token() == Token(TokenType.FLOAT, "123.123", Index(2, 0, _file))

    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(3, 0, _file))
    assert lexer.next_token() == Token(
        TokenType.STRING, "base string", Index(3, 0, _file)
    )

    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(5, 0, _file))
    assert lexer.next_token() == Token(TokenType.EOF, "EOF", Index(5, 0, _file))


def test_basic_math() -> None:
    _file = get_file("test_basic_math.eiko")
    lexer = Lexer(_file)

    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(0, 0, _file))
    assert lexer.next_token() == Token(TokenType.INTEGER, "1", Index(0, 0, _file))
    assert lexer.next_token() == Token(TokenType.ARITHMETIC_OP, "+", Index(0, 2, _file))
    assert lexer.next_token() == Token(TokenType.INTEGER, "4", Index(0, 4, _file))
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "//", Index(0, 6, _file)
    )
    assert lexer.next_token() == Token(TokenType.INTEGER, "2", Index(0, 9, _file))
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "+", Index(0, 11, _file)
    )
    assert lexer.next_token() == Token(TokenType.INTEGER, "3", Index(0, 13, _file))

    assert lexer.next_token() == Token(TokenType.INDENT, "", Index(1, 0, _file))
    assert lexer.next_token() == Token(TokenType.INTEGER, "1", Index(1, 0, _file))
    assert lexer.next_token() == Token(TokenType.ARITHMETIC_OP, "+", Index(1, 2, _file))
    assert lexer.next_token() == Token(TokenType.INTEGER, "2", Index(1, 4, _file))
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "//", Index(1, 6, _file)
    )
    assert lexer.next_token() == Token(TokenType.ARITHMETIC_OP, "-", Index(1, 9, _file))
    assert lexer.next_token() == Token(TokenType.INTEGER, "3", Index(1, 10, _file))
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "**", Index(1, 11, _file)
    )
    assert lexer.next_token() == Token(TokenType.INTEGER, "2", Index(1, 13, _file))
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "+", Index(1, 15, _file)
    )
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "-", Index(1, 17, _file)
    )
    assert lexer.next_token() == Token(TokenType.INTEGER, "7", Index(1, 18, _file))
    assert lexer.next_token() == Token(
        TokenType.ARITHMETIC_OP, "*", Index(1, 20, _file)
    )
    assert lexer.next_token() == Token(TokenType.INTEGER, "2", Index(1, 22, _file))
    # Can't be bothered finishing this rn
