"""
Handlers are a way to describe to Eikobot how something should be deployed.
"""
from dataclasses import dataclass
from typing import Any, Union

from . import logger
from .compiler.definitions.base_model import BaseModel
from .compiler.definitions.base_types import EikoResource


@dataclass
class HandlerContext:
    """A HandlerContext keeps track of things required for a deployment."""

    raw_resource: EikoResource

    def __post_init__(self) -> None:
        self.resource: Union[dict, BaseModel]
        self.changes: dict[str, Any] = {}
        self.deployed = False
        self.updated = False
        self.failed = False
        self.promises = self.raw_resource.promises
        self.name = self.raw_resource.index()

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

    async def execute(self, ctx: HandlerContext) -> None:
        raise NotImplementedError

    async def resolve_promises(self, ctx: HandlerContext) -> None:
        pass


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
