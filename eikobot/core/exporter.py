"""
The exporter takes the output from the compiler
and turns it in tasks the deployer understands.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Union

from . import logger
from .compiler import Compiler, CompilerContext
from .errors import EikoExportError, EikoInternalError
from .handlers import Handler, HandlerContext
from .helpers import EikoDict, EikoList, EikoResource


@dataclass
class Task:
    """A task is a piece of work the backend needs to do."""

    task_id: str
    ctx: HandlerContext
    handler: Optional[Handler]

    def __post_init__(self) -> None:
        self.dependants: list["Task"] = []
        self.depends_on: list["Task"] = []
        self.depends_on_copy: list["Task"] = []
        self._done_cb: Optional[Callable[[], None]] = None
        self._failure_cb: Optional[Callable[[], None]] = None

    def init(
        self,
        done_cb: Optional[Callable[[], None]] = None,
        failure_cb: Optional[Callable[[], None]] = None,
    ) -> None:
        """Resets a task and it's sub tasks so they can run again."""
        self._done_cb = done_cb
        self._failure_cb = failure_cb
        self.depends_on_copy = self.depends_on.copy()
        for dependant in self.dependants:
            dependant.init(done_cb, failure_cb)

    async def execute(self) -> None:
        """Executes the task, than let's it's dependants know it's done."""
        logger.info(f"starting task '{self.task_id}'")
        self._resolve_promises()
        if self.handler is not None:
            await self.handler.execute(self.ctx)
        else:
            raise EikoInternalError(
                "Deployer failed to execute a task because a handler was missing. "
            )

        for name, promise in self.ctx.raw_resource.promises.items():
            if promise.value is None:
                logger.error(
                    f"Resource '{self.task_id}' was deployed, "
                    f"but promise '{name}' was not fullfilled."
                )
                if self._failure_cb is not None:
                    self._failure_cb()
                return

            self.ctx.raw_resource.properties[name] = promise.value

        self.ctx.resource = self.ctx.raw_resource.to_py()

        if self.ctx.failed or not self.ctx.deployed:
            logger.error(f"Failed task '{self.task_id}'")
            if self._failure_cb is not None:
                self._failure_cb()
            return

        logger.debug(f"Done executing task '{self.task_id}'")
        for sub_task in self.dependants:
            sub_task.remove_dep(self)

        if self._done_cb is not None:
            self._done_cb()

    def _resolve_promises(self) -> None:
        logger.debug(f"Task '{self.task_id}' is resolving extenral promises.")
        for name, promise in self.ctx.raw_resource.get_external_promises():
            if promise.value is None:
                raise EikoInternalError(
                    "An external promise that should ahve been resolved was not. "
                    "This should have been caught earlier.",
                    token=promise.token,
                )

            self.ctx.raw_resource.properties[name] = promise.value

        self.ctx.resource = self.ctx.raw_resource.to_py()

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
                sub_task.add_dependant(self)
        else:
            for sub_sub_task in sub_task.depends_on:
                self.add_depends_on(sub_sub_task)
                if self.handler is not None:
                    sub_sub_task.add_dependant(self)

    def add_dependant(self, task: "Task") -> None:
        if task not in self.dependants:
            self.dependants.append(task)

    def add_depends_on(self, task: "Task") -> None:
        if task not in self.depends_on:
            self.depends_on.append(task)

    def process_promise(self, super_task: "Task") -> None:
        """
        Calculates dependencies for a task that depends on a promise.

        The passed super_task should be the one releasing the promise.
        """
        if super_task.handler is None:
            raise EikoExportError(
                f"Resource '{super_task.ctx.raw_resource.type.name}' "
                "has promises but no handler.",
            )

        self.process_sub_task(super_task)


class Exporter:
    """
    The exporter takes the output from the compiler
    and turns it in tasks the deployer understands.
    """

    def __init__(self) -> None:
        self.task_index: dict[str, Task] = {}
        self.base_tasks: list[Task] = []
        self.total_tasks: int = 0

    def export_from_file(self, file: Path) -> None:
        """Compiles a file and exports the tasks."""
        logger.debug("Constructing task dependency trees.")
        compiler = Compiler()
        compiler.compile(file)
        self.export_from_context(compiler.context)

    def export_from_context(self, context: CompilerContext) -> None:
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
            self.total_tasks += 1

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

        for name, promise in resource.get_external_promises():
            super_task = self.task_index.get(promise.parent.index())
            if super_task is None:
                raise EikoExportError(
                    f"Task '{task_id}' depends on promise "
                    f"'{promise.parent.index()}.{name}', but this promise has no associated task."
                )
            task.process_promise(super_task)

        self.task_index[task_id] = task
        if task.handler is not None and not task.depends_on:
            self.base_tasks.append(task)

        return task
