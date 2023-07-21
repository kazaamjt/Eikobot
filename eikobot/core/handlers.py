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
        logger.debug(msg, pre=f"[{self.name}] ")

    def info(self, msg: str) -> None:
        logger.info(msg, pre=f"[{self.name}] ")

    def warning(self, msg: str) -> None:
        logger.warning(msg, pre=f"[{self.name}] ")

    def error(self, msg: str) -> None:
        logger.error(msg, pre=f"[{self.name}] ")


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
        ctx.info(f"Task '{ctx.name}' would execute.")


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
            logger.debug(f"Reading resource '{ctx.raw_resource.index()}'.")
            await self.read(ctx)
        except EikoCRUDHanlderMethodNotImplemented:
            pass

        if not ctx.deployed:
            try:
                logger.debug(f"Deploying resource '{ctx.raw_resource.index()}'.")
                await self.create(ctx)
            except EikoCRUDHanlderMethodNotImplemented:
                logger.error(
                    "Tried to deploy resource, but handler is missing a create method."
                )
                return
        else:
            if ctx.changes:
                try:
                    ctx.deployed = False
                    logger.debug(f"Updating resource '{ctx.raw_resource.index()}'.")
                    await self.update(ctx)
                except EikoCRUDHanlderMethodNotImplemented:
                    logger.warning(
                        "Read method returned changes for handler without update method."
                    )
            else:
                logger.debug(
                    f"Resource '{ctx.raw_resource.index()}' is in its desired state."
                )

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
            logger.debug(f"Reading resource '{ctx.raw_resource.index()}'.")
            await self.read(ctx)
        except EikoCRUDHanlderMethodNotImplemented:
            logger.info(f"Resource '{ctx.name}' would be created.")
        except EikoUnresolvedPromiseError:
            logger.info(
                f"Resource '{ctx.name}' relies on promises that are unresolved and thus its state is unknown."
            )
            return

        if ctx.deployed:
            if not ctx.changes:
                logger.info(f"Resource '{ctx.name}' is in its desired state.")
            else:
                logger.info(
                    f"Resource '{ctx.name}' would be updated. (changes: {ctx.changes})"
                )
        else:
            logger.info(f"Resource '{ctx.name}' would be created.")
