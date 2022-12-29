# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
from pathlib import Path

import pytest

from eikobot.core.deployer import Deployer


@pytest.mark.asyncio
async def test_promises(eiko_promises_file: Path) -> None:
    deployer = Deployer()
    await deployer.deploy_from_file(eiko_promises_file)
