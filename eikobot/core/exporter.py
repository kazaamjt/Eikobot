"""
The exporter takes the output from the compiler
and turns it in tasks the deployer understands.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Union

from . import logger
from .compiler import Compiler, CompilerContext
from .errors import EikoInternalError
from .handlers import Handler, HandlerContext
from .helpers import EikoDict, EikoList, EikoResource


@dataclass
class Task:
    """A task is a piece of work the backend needs to do."""

    task_id: str
    ctx: Optional[HandlerContext]
    handler: Optional[Handler]

    def __post_init__(self) -> None:
        self.dependants: list["Task"] = []
        self.depends_on: list["Task"] = []
        self.depends_on_copy: list["Task"] = []
        self.done_cb: Optional[Callable[[], None]] = None

    def init(self, done_cb: Optional[Callable[[], None]] = None) -> None:
        """Resets a task and it's sub tasks so they can run again."""
        self.done_cb = done_cb
        self.depends_on_copy = self.depends_on.copy()
        for dependant in self.dependants:
            dependant.init(done_cb)

    async def execute(self) -> None:
        """Executes the task, than let's it's dependants know it's done."""
        logger.debug(f"Executing task '{self.task_id}'")
        if self.handler is not None and self.ctx is not None:
            await self.handler.execute(self.ctx)
        else:
            raise EikoInternalError(
                "Deployer failed to execute a task because a handler or context was missing. "
            )

        if self.ctx.failed:
            logger.error(f"Failed task '{self.task_id}'")
        else:
            for sub_task in self.dependants:
                sub_task.remove_dep(self)
            logger.debug(f"Done executing task '{self.task_id}'")
            if self.done_cb is not None:
                self.done_cb()

    def remove_dep(self, task: "Task") -> None:
        self.depends_on_copy.remove(task)

    def process_sub_task(self, sub_task: "Task") -> None:
        """
        Adds a task as a dependancy for this task.
        Sets up in such a way that dependancies are correct.
        """
        if sub_task.handler is not None:
            self.depends_on.append(sub_task)
            if self.handler is not None:
                sub_task.dependants.append(self)
        else:
            for sub_sub_task in sub_task.depends_on:
                self.depends_on.append(sub_sub_task)
                if self.handler is not None:
                    sub_sub_task.dependants.append(self)


class Exporter:
    """
    The exporter takes the output from the compiler
    and turns it in tasks the deployer understands.
    """

    def __init__(self) -> None:
        self.task_index: dict[str, Task] = {}
        self.base_tasks: list[Task] = []

    def export_from_file(self, file: Path) -> list[Task]:
        """Compiles a file and exports the tasks."""
        logger.debug("Constructing task dependency trees.")
        compiler = Compiler()
        compiler.compile(file)
        return self.export_from_context(compiler.context)

    def export_from_context(self, context: CompilerContext) -> list[Task]:
        """
        Walks through a compiler context and exports it as a set fo tasks.
        """
        values = list(context.storage.values())
        values.extend(context.orphans)

        for value in values:
            if isinstance(value, EikoResource):
                self._parse_task(value)
            elif isinstance(value, (EikoList, EikoDict)):
                self._parse_multi(value)

        return self.base_tasks

    def _parse_multi(self, value: Union[EikoList, EikoDict]) -> list[Task]:
        tasks: list[Task] = []
        if isinstance(value, EikoList):
            item_list = value.elements

        elif isinstance(value, EikoDict):
            item_list = list(value.elements.values())

        for item in item_list:
            if isinstance(item, EikoResource):
                tasks.append(self._parse_task(item))
            elif isinstance(item, (EikoList, EikoDict)):
                tasks.extend(self._parse_multi(item))

        return tasks

    def _parse_task(self, resource: EikoResource) -> Task:
        task_id = resource.index()
        pre_task = self.task_index.get(task_id)
        if pre_task is not None:
            return pre_task

        handler = None
        if resource.class_ref.handler is not None:
            handler = resource.class_ref.handler()

        task = Task(
            resource.index(),
            HandlerContext(resource),
            handler,
        )

        for value in resource.properties.values():
            if isinstance(value, EikoResource):
                task.process_sub_task(self._parse_task(value))
            elif isinstance(value, (EikoList, EikoDict)):
                for item in self._parse_multi(value):
                    task.process_sub_task(item)

        self.task_index[task_id] = task
        if task.handler is not None and not task.depends_on:
            self.base_tasks.append(task)

        return task
