"""
The deployer takes the output of the exporter
and goes through the tasks of deploying.
"""
import asyncio
from dataclasses import dataclass
from pathlib import Path

from . import logger
from .exporter import Exporter, Task


@dataclass
class DeployProgress:
    """
    Helper class for deployer to display how far along it is.
    """

    total: int
    log: bool = False
    done: int = 0


class Deployer:
    """
    The deployer takes the output of the exporter
    and goes through the tasks of deploying.
    """

    def __init__(self) -> None:
        self.asyncio_tasks: list[asyncio.Task] = []
        self.log_progress = False
        self.progress = DeployProgress(0)
        self.failed = False

    async def deploy(self, exporter: Exporter, log_progress: bool = False) -> None:
        """
        Given a set of Tasks, walks through them and makes sure they're all done.
        """
        self.failed = False
        self.log_progress = log_progress
        self.progress = DeployProgress(exporter.total_tasks, log_progress)
        for task in exporter.base_tasks:
            task.init(self._done_cb, self._failure_cb)
            self._create_task(task)

        while self.asyncio_tasks:
            await asyncio.gather(*self.asyncio_tasks)

        logger.info("Cleaning up.")
        for task in exporter.task_index.values():
            if task.handler is not None:
                await task.handler.cleanup(task.ctx)

    async def dry_run(self, exporter: Exporter) -> None:
        """Executes a dry run of all tasks."""
        for task in exporter.base_tasks:
            task.init()

        for task in exporter.task_index.values():
            if task.handler is not None:
                task.ctx.resource = task.ctx.raw_resource.to_py()
                await task.handler.__dry_run__(task.ctx)

    async def deploy_from_file(self, eiko_file: Path) -> None:
        """Helper funcion meant mostly for testing."""
        exporter = Exporter()
        exporter.export_from_file(eiko_file)
        await self.deploy(exporter)

    def _create_task(self, task: Task) -> None:
        asyncio_task = asyncio.create_task(self._execute_task(task))
        self.asyncio_tasks.append(asyncio_task)

    async def _execute_task(self, task: Task) -> None:
        await task.execute()
        for sub_task in task.dependants:
            if not sub_task.depends_on_copy:
                self._create_task(sub_task)

        asyncio_task = asyncio.current_task()
        if asyncio_task is not None:
            self.asyncio_tasks.remove(asyncio_task)

    def _done_cb(self) -> None:
        self.progress.done += 1
        if self.progress.log:
            logger.info(f"{self.progress.done} of {self.progress.total} tasks done.")

    def _failure_cb(self) -> None:
        self.failed = True
