# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
from pathlib import Path

import pytest

from eikobot.core.deployer import Deployer
from eikobot.core.exporter import Exporter


@pytest.mark.asyncio
async def test_deploy(eiko_deploy_file: Path) -> None:
    exporter = Exporter()
    base_tasks = exporter.export_from_file(eiko_deploy_file)
    deployer = Deployer()
    await deployer.deploy(base_tasks)

    base_handler_1 = base_tasks[0].handler
    base_handler_2 = base_tasks[1].handler
    base_handler_3 = base_tasks[2].handler

    assert base_handler_1.created  # type: ignore
    assert base_handler_2.created  # type: ignore
    assert base_handler_3.created  # type: ignore
    assert base_handler_1.create_called == 1  # type: ignore
    assert base_handler_2.create_called == 1  # type: ignore
    assert base_handler_3.create_called == 1  # type: ignore
    assert base_handler_1.update_called == 0  # type: ignore
    assert base_handler_2.update_called == 0  # type: ignore
    assert base_handler_3.update_called == 0  # type: ignore

    mid_handler_1 = base_tasks[0].dependants[0].handler
    mid_handler_2 = base_tasks[1].dependants[0].handler
    mid_handler_3 = base_tasks[2].dependants[0].handler

    assert mid_handler_1.created  # type: ignore
    assert mid_handler_2.created  # type: ignore
    assert mid_handler_3.created  # type: ignore
    assert mid_handler_1.create_called == 1  # type: ignore
    assert mid_handler_2.create_called == 1  # type: ignore
    assert mid_handler_3.create_called == 1  # type: ignore
    assert mid_handler_1.update_called == 0  # type: ignore
    assert mid_handler_2.update_called == 0  # type: ignore
    assert mid_handler_3.update_called == 0  # type: ignore

    top_handler_1 = base_tasks[0].dependants[0].dependants[0].handler
    top_handler_2 = base_tasks[0].dependants[0].dependants[1].handler

    assert top_handler_1.created  # type: ignore
    assert top_handler_2.created  # type: ignore
    assert top_handler_1.create_called == 1  # type: ignore
    assert top_handler_2.create_called == 1  # type: ignore
    assert top_handler_1.update_called == 0  # type: ignore
    assert top_handler_2.update_called == 0  # type: ignore

    await deployer.deploy(base_tasks)

    assert base_handler_1.created  # type: ignore
    assert base_handler_2.created  # type: ignore
    assert base_handler_3.created  # type: ignore
    assert base_handler_1.create_called == 2  # type: ignore
    assert base_handler_2.create_called == 2  # type: ignore
    assert base_handler_3.create_called == 2  # type: ignore
    assert base_handler_1.update_called == 0  # type: ignore
    assert base_handler_2.update_called == 0  # type: ignore
    assert base_handler_3.update_called == 0  # type: ignore

    mid_handler_1 = base_tasks[0].dependants[0].handler
    mid_handler_2 = base_tasks[1].dependants[0].handler
    mid_handler_3 = base_tasks[2].dependants[0].handler

    assert mid_handler_1.created  # type: ignore
    assert mid_handler_2.created  # type: ignore
    assert mid_handler_3.created  # type: ignore
    assert mid_handler_1.create_called == 1  # type: ignore
    assert mid_handler_2.create_called == 1  # type: ignore
    assert mid_handler_3.create_called == 1  # type: ignore
    assert mid_handler_1.update_called == 0  # type: ignore
    assert mid_handler_2.update_called == 0  # type: ignore
    assert mid_handler_3.update_called == 0  # type: ignore

    top_handler_1 = base_tasks[0].dependants[0].dependants[0].handler
    top_handler_2 = base_tasks[0].dependants[0].dependants[1].handler

    assert top_handler_1.created  # type: ignore
    assert top_handler_2.created  # type: ignore
    assert top_handler_1.create_called == 1  # type: ignore
    assert top_handler_2.create_called == 1  # type: ignore
    assert top_handler_1.update_called == 1  # type: ignore
    assert top_handler_2.update_called == 1  # type: ignore

    await deployer.deploy(base_tasks)

    assert base_handler_1.created  # type: ignore
    assert base_handler_2.created  # type: ignore
    assert base_handler_3.created  # type: ignore
    assert base_handler_1.create_called == 3  # type: ignore
    assert base_handler_2.create_called == 3  # type: ignore
    assert base_handler_3.create_called == 3  # type: ignore
    assert base_handler_1.update_called == 0  # type: ignore
    assert base_handler_2.update_called == 0  # type: ignore
    assert base_handler_3.update_called == 0  # type: ignore

    mid_handler_1 = base_tasks[0].dependants[0].handler
    mid_handler_2 = base_tasks[1].dependants[0].handler
    mid_handler_3 = base_tasks[2].dependants[0].handler

    assert mid_handler_1.created  # type: ignore
    assert mid_handler_2.created  # type: ignore
    assert mid_handler_3.created  # type: ignore
    assert mid_handler_1.create_called == 1  # type: ignore
    assert mid_handler_2.create_called == 1  # type: ignore
    assert mid_handler_3.create_called == 1  # type: ignore
    assert mid_handler_1.update_called == 0  # type: ignore
    assert mid_handler_2.update_called == 0  # type: ignore
    assert mid_handler_3.update_called == 0  # type: ignore

    top_handler_1 = base_tasks[0].dependants[0].dependants[0].handler
    top_handler_2 = base_tasks[0].dependants[0].dependants[1].handler

    assert top_handler_1.created  # type: ignore
    assert top_handler_2.created  # type: ignore
    assert top_handler_1.create_called == 1  # type: ignore
    assert top_handler_2.create_called == 1  # type: ignore
    assert top_handler_1.update_called == 2  # type: ignore
    assert top_handler_2.update_called == 2  # type: ignore
