# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
# pylint: disable=redefined-outer-name
"""
conftest.py is a special pytest file.
It is used to store fixtures for easy reuse.
see https://docs.pytest.org/en/6.2.x/fixture.html
"""
import uuid
from pathlib import Path

import pytest


def get_file(name: str) -> Path:
    return Path(__file__).resolve().parent / "files" / name


def get_std_file(name: str) -> Path:
    return Path(__file__).resolve().parent / "std/files" / name


@pytest.fixture
def tmp_eiko_file(tmp_path: Path) -> Path:
    """Temporary file using tmp_path fixture"""
    tmp_file = tmp_path / (str(uuid.uuid4()) + ".eiko")
    return tmp_file


@pytest.fixture
def eiko_file_1() -> Path:
    _file = get_file("file_1.eiko")
    return _file


@pytest.fixture
def eiko_file_2() -> Path:
    _file = get_file("file_2.eiko")
    return _file


@pytest.fixture
def eiko_file_3() -> Path:
    _file = get_file("file_3.eiko")
    return _file


@pytest.fixture
def eiko_base_type_file() -> Path:
    _file = get_file("test_base_types.eiko")
    return _file


@pytest.fixture
def eiko_basic_ops_file() -> Path:
    _file = get_file("test_basic_ops.eiko")
    return _file


@pytest.fixture
def eiko_std_file() -> Path:
    _file = get_file("test_std.eiko")
    return _file


@pytest.fixture
def eiko_from_import_file() -> Path:
    _file = get_file("test_from_import.eiko")
    return _file


@pytest.fixture
def eiko_f_string_file() -> Path:
    _file = get_file("test_f_string.eiko")
    return _file


@pytest.fixture
def nested_properties_file() -> Path:
    _file = get_file("test_nested_properties.eiko")
    return _file


@pytest.fixture
def eiko_if_elif_else_file() -> Path:
    _file = get_file("test_if_elif_else.eiko")
    return _file


@pytest.fixture
def eiko_typedef() -> Path:
    _file = get_file("test_typedef.eiko")
    return _file


@pytest.fixture
def eiko_std_regex_match() -> Path:
    _file = get_std_file("regex_match.eiko")
    return _file


@pytest.fixture
def eiko_std_file_file() -> Path:
    _file = get_std_file("file.eiko")
    return _file


@pytest.fixture
def eiko_union_file() -> Path:
    _file = get_file("test_union.eiko")
    return _file


@pytest.fixture
def eiko_list_file() -> Path:
    _file = get_file("test_list.eiko")
    return _file


@pytest.fixture
def eiko_dict_file() -> Path:
    _file = get_file("test_dict.eiko")
    return _file


@pytest.fixture
def eiko_decorator_file() -> Path:
    _file = get_file("test_decorator.eiko")
    return _file


@pytest.fixture
def eiko_multi_import_file() -> Path:
    _file = get_file("test_multi_import.eiko")
    return _file


@pytest.fixture
def eiko_std_ipaddr() -> Path:
    _file = get_std_file("test_ipaddr.eiko")
    return _file
