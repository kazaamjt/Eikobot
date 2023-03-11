# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
from pathlib import Path

from eikobot.core.exporter import Exporter
from eikobot.core.handlers import CRUDHandler


def test_exporter(eiko_exporter_and_handlers: Path) -> None:
    exporter = Exporter()
    exporter.export_from_file(eiko_exporter_and_handlers)
    assert len(exporter.base_tasks) == 1

    bot_task = exporter.base_tasks[0]
    assert bot_task.task_id == "BotRes-192.168.0.100"
    assert isinstance(bot_task.handler, CRUDHandler)
    assert len(bot_task.depends_on) == 0
    assert len(bot_task.dependants) == 2

    top_task_1 = bot_task.dependants[0]
    assert top_task_1.task_id == "TopRes-192.168.0.1"
    assert isinstance(top_task_1.handler, CRUDHandler)
    assert len(top_task_1.depends_on) == 1
    assert top_task_1.depends_on[0] == bot_task
    assert len(top_task_1.dependants) == 0
    assert top_task_1 in bot_task.dependants

    top_task_2 = bot_task.dependants[1]
    assert top_task_2.task_id == "TopRes-192.168.0.2"
    assert isinstance(top_task_2.handler, CRUDHandler)
    assert len(top_task_2.depends_on) == 1
    assert top_task_2.depends_on[0] == bot_task
    assert len(top_task_2.dependants) == 0
    assert top_task_2 in bot_task.dependants
