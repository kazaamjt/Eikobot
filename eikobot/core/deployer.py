"""
The deployer takes the output of the exporter
and goes through the tasks of deploying.
"""
import asyncio

from .exporter import Task


class Deployer:
    """
    The deployer takes the output of the exporter
    and goes through the tasks of deploying.
    """

    def __init__(self) -> None:
        self.current_tasks: list[asyncio.Task] = []

    async def deploy(self, tasks: list[Task]) -> None:
        """
        Given a set of Tasks, walks through them and makes sure they're all done.
        """
        for task in tasks:
            task.init()
            self._create_task(task)

        while self.current_tasks:
            await asyncio.gather(*self.current_tasks)

    def _create_task(self, task: Task) -> None:
        asyncio_task = asyncio.create_task(self._execute_task(task))
        self.current_tasks.append(asyncio_task)

    async def _execute_task(self, task: Task) -> None:
        await task.execute()
        for sub_task in task.dependants:
            if not sub_task.depends_on_copy:
                self._create_task(sub_task)

        asyncio_task = asyncio.current_task()
        if asyncio_task is not None:
            self.current_tasks.remove(asyncio_task)
