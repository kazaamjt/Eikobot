# pylint: disable=no-self-use
"""
Handlers are a way to describe to Eikobot how something should be deployed.
"""
from dataclasses import dataclass
from typing import Any

from .compiler.definitions.base_types import EikoResource


@dataclass
class HandlerContext:
    """A HandlerContext keeps track of things required for a deployment."""

    resource: EikoResource

    def __post_init__(self) -> None:
        self.changes: dict[str, Any] = {}
        self.deployed = False
        self.updated = False

    def add_change(self, key: str, value: Any) -> None:
        self.changes[key] = value


class Handler:
    """A handler implements methods for a resource to be managed."""

    resource: str


class EikoCRUDHanlderMethodNotImplemented(Exception):
    """Raised if a method is not implemented."""


class CRUDHandler(Handler):
    """
    A crud resource handler implements python code that handles
    the deployment and updating of resources in python code.
    """

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

    async def create(self, ctx: HandlerContext) -> None:
        raise EikoCRUDHanlderMethodNotImplemented

    async def read(self, ctx: HandlerContext) -> None:
        raise EikoCRUDHanlderMethodNotImplemented

    async def update(self, ctx: HandlerContext) -> None:
        raise EikoCRUDHanlderMethodNotImplemented

    async def delete(self, ctx: HandlerContext) -> None:
        raise EikoCRUDHanlderMethodNotImplemented
