# pylint: disable=missing-module-docstring
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
from typing import Iterable

import pytest


def get_file(name: str) -> Path:
    return Path(__file__).resolve().parent / "files" / name


@pytest.fixture
def tmp_eiko_file(tmp_path: Path) -> Iterable[Path]:
    """Temporary file using tmp_path fixture"""
    tmp_file = tmp_path / (str(uuid.uuid4()) + ".eiko")
    yield tmp_file


@pytest.fixture
def eiko_file_1() -> Iterable[Path]:
    tmp_file = get_file("file_1.eiko")
    yield tmp_file


@pytest.fixture
def eiko_file_2() -> Iterable[Path]:
    tmp_file = get_file("file_2.eiko")
    yield tmp_file


@pytest.fixture
def eiko_file_3() -> Iterable[Path]:
    tmp_file = get_file("file_3.eiko")
    yield tmp_file


@pytest.fixture
def eiko_base_type_file() -> Iterable[Path]:
    tmp_file = get_file("test_base_types.eiko")
    yield tmp_file


@pytest.fixture
def eiko_basic_ops_file() -> Iterable[Path]:
    tmp_file = get_file("test_basic_ops.eiko")
    yield tmp_file


@pytest.fixture
def eiko_std_file() -> Iterable[Path]:
    tmp_file = get_file("test_std.eiko")
    yield tmp_file


@pytest.fixture
def eiko_from_import_file() -> Iterable[Path]:
    tmp_file = get_file("test_from_import.eiko")
    yield tmp_file


@pytest.fixture
def eiko_f_string_file() -> Iterable[Path]:
    tmp_file = get_file("test_f_string.eiko")
    yield tmp_file


@pytest.fixture
def nested_properties_file() -> Iterable[Path]:
    tmp_file = get_file("test_nested_properties.eiko")
    yield tmp_file
