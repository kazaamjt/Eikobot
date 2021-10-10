# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
"""
conftest.py is a special pytest file.
It is used to store fixtures for easy reuse.
see https://docs.pytest.org/en/6.2.x/fixture.html
"""
import uuid
from pathlib import Path
from typing import Iterable

import pytest


@pytest.fixture
def tmp_eiko_file(tmp_path: Path) -> Iterable[Path]:
    """Temporary file using tmp_path fixture"""
    tmp_file = tmp_path / (str(uuid.uuid4()) + ".eiko")
    yield tmp_file
