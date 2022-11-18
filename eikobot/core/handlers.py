# pylint: disable=no-self-use
"""
Handlers are a way to describe to Eikobot how something should be deployed.
"""
from dataclasses import dataclass
from typing import Any

from . import logger
from .compiler.definitions.base_types import EikoResource


@dataclass
class HandlerContext:
    """A HandlerContext keeps track of things required for a deployment."""

    resource: EikoResource

    def __post_init__(self) -> None:
        self.changes: dict[str, Any] = {}
        self.deployed = False
        self.updated = False
        self.failed = False

    def add_change(self, key: str, value: Any) -> None:
        self.changes[key] = value


class Handler:
    """A handler implements methods for a resource to be managed."""

    resource: str

    async def execute(self, ctx: HandlerContext) -> None:
        raise NotImplementedError


class EikoCRUDHanlderMethodNotImplemented(Exception):
    """Raised if a method is not implemented."""


class CRUDHandler(Handler):
    """
    A CRUD resource handler implements python code that handles
    the deployment and updating of resources in python code.
    This handler is blocking. It is highly recommended to use
    the non blocking AsyncCrudHandler instead.
    """

    async def execute(self, ctx: HandlerContext) -> None:
        ctx.failed = False
        try:
            self.read(ctx)
        except EikoCRUDHanlderMethodNotImplemented:
            pass

        if not ctx.deployed:
            try:
                self.create(ctx)
            except EikoCRUDHanlderMethodNotImplemented:
                logger.error(
                    "Tried to deploy resource, but handler is missing a create method."
                )
                return
        else:
            if ctx.changes:
                try:
                    ctx.deployed = False
                    self.update(ctx)
                except EikoCRUDHanlderMethodNotImplemented:
                    logger.warning(
                        "Read method returned changes for handler without update method."
                    )

        if not ctx.deployed:
            ctx.failed = True

    def create(self, ctx: HandlerContext) -> None:
        raise EikoCRUDHanlderMethodNotImplemented

    def read(self, ctx: HandlerContext) -> None:
        raise EikoCRUDHanlderMethodNotImplemented

    def update(self, ctx: HandlerContext) -> None:
        raise EikoCRUDHanlderMethodNotImplemented

    def delete(self, ctx: HandlerContext) -> None:
        raise EikoCRUDHanlderMethodNotImplemented


class AsyncCRUDHandler(Handler):
    """
    An async crud resource handler is like a CRUDHandler,
    but it's methods are async.
    """

    async def execute(self, ctx: HandlerContext) -> None:
        ctx.failed = False
        ctx.deployed = False
        try:
            await self.read(ctx)
        except EikoCRUDHanlderMethodNotImplemented:
            pass

        if not ctx.deployed:
            try:
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
                    await self.update(ctx)
                except EikoCRUDHanlderMethodNotImplemented:
                    logger.warning(
                        "Read method returned changes for handler without update method."
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
