# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
import pytest

from eikobot import __version__
from eikobot.core.package_manager import PackageData
from eikobot.core.project import eiko_version_match


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (f">={__version__}", True),
        (f"=={__version__}", True),
        (f"!={__version__}", False),
        (f"<={__version__}", True),
        (f">{__version__}", False),
        (f"<{__version__}", False),
        (f"=={__version__},>={__version__}", True),
        (f"=={__version__},!={__version__}", False),
    ],
)
def test_package_version_matching(test_input: str, expected: bool) -> None:
    pkg_data = PackageData(
        **{  # type: ignore
            "name": "test-pkg",
            "source_dir": ".",
            "eikobot_version": test_input,
        }
    )
    assert pkg_data.eikobot_version is not None
    assert expected == eiko_version_match(pkg_data.eikobot_version)
