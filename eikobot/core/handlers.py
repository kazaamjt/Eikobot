"""
Handlers are a way to describe to Eikobot how something should be deployed.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Union

from . import logger
from .compiler.definitions.base_model import BaseModel
from .compiler.definitions.base_types import EikoResource
from .errors import EikoUnresolvedPromiseError

CACHE_DIR = Path(".eikobot_cache")
CACHE_DIR.mkdir(exist_ok=True)


@dataclass
class HandlerContext:
    """A HandlerContext keeps track of things required for a deployment."""

    raw_resource: EikoResource
    task_id: str

    def __post_init__(self) -> None:
        self.resource: Union[dict, BaseModel]
        self.changes: dict[str, Any] = {}
        self.deployed = False
        self.updated = False
        self.failed = False
        self.promises = self.raw_resource.promises
        self.name = self.raw_resource.index()
        self.extras: dict[str, Any] = {}
        self.task_cache = CACHE_DIR / self.normalized_task_id()

        self.task_cache.mkdir(exist_ok=True)

    def normalized_task_id(self) -> str:
        """
        Removes backslashes, forward slashes and : from the task_id
        so it can be used for paths on both unix and windows.
        """
        _normalized = self.task_id.replace("\\", "-")
        _normalized = _normalized.replace("/", "-")
        _normalized = _normalized.replace(" ", "")
        return _normalized.replace(":", ".")

    def add_change(self, key: str, value: Any) -> None:
        self.changes[key] = value

    def debug(self, msg: str) -> None:
        logger.debug(f"[{self.name}] {msg}")

    def info(self, msg: str) -> None:
        logger.info(f"[{self.name}] {msg}")

    def warning(self, msg: str) -> None:
        logger.warning(f"[{self.name}] {msg}")

    def error(self, msg: str) -> None:
        logger.error(f"[{self.name}] {msg}")


class Handler:
    """A handler implements methods for a resource to be managed."""

    __eiko_resource__: str

    async def __pre__(self, ctx: HandlerContext) -> None:
        pass

    async def execute(self, ctx: HandlerContext) -> None:
        raise NotImplementedError

    async def resolve_promises(self, ctx: HandlerContext) -> None:
        pass

    async def __post__(self, ctx: HandlerContext) -> None:
        pass

    async def cleanup(self, ctx: HandlerContext) -> None:
        pass

    async def __dry_run__(self, ctx: HandlerContext) -> None:
        ctx.info("Task would execute.")


class EikoCRUDHanlderMethodNotImplemented(Exception):
    """Raised if a method is not implemented."""


class CRUDHandler(Handler):
    """
    An async crud resource handler is like a CRUDHandler,
    but it's methods are async.
    """

    async def execute(self, ctx: HandlerContext) -> None:
        ctx.failed = False
        ctx.deployed = False
        try:
            ctx.debug("Reading resource.")
            await self.read(ctx)
        except EikoCRUDHanlderMethodNotImplemented:
            pass

        if not ctx.deployed:
            try:
                ctx.debug("Deploying resource.")
                await self.create(ctx)
            except EikoCRUDHanlderMethodNotImplemented:
                ctx.error(
                    "Tried to deploy resource, but handler is missing a create method."
                )
                return
        else:
            if ctx.changes:
                try:
                    ctx.deployed = False
                    ctx.debug("Updating resource.")
                    await self.update(ctx)
                except EikoCRUDHanlderMethodNotImplemented:
                    ctx.warning(
                        "Read method returned changes for handler without update method."
                    )
            else:
                ctx.debug("Resource is in its desired state.")

        if not ctx.deployed:
            ctx.failed = True

    async def create(self, ctx: HandlerContext) -> None:
        raise EikoCRUDHanlderMethodNotImplemented

    async def read(self, ctx: HandlerContext) -> None:
        raise EikoCRUDHanlderMethodNotImplemented

    async def update(self, ctx: HandlerContext) -> None:
        raise EikoCRUDHanlderMethodNotImplemented

    async def delete(self, ctx: HandlerContext) -> None:
        raise EikoCRUDHanlderMethodNotImplemented

    async def __dry_run__(self, ctx: HandlerContext) -> None:
        try:
            ctx.debug(f"Reading resource '{ctx.raw_resource.index()}'.")
            await self.read(ctx)
        except EikoCRUDHanlderMethodNotImplemented:
            ctx.info("Resource would be created.")
        except EikoUnresolvedPromiseError:
            ctx.info(
                "Resource relies on promises that are unresolved and thus its state is unknown."
            )
            return

        if ctx.deployed:
            if not ctx.changes:
                ctx.info("Resource is in its desired state.")
            else:
                ctx.info(f"Resource would be updated. (changes: {ctx.changes})")
        elif ctx.failed:
            ctx.error("Resource is in a failed state!")
        else:
            ctx.info("Resource would be created.")
