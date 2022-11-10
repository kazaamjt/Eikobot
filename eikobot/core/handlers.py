# pylint: disable=no-self-use
"""
Handlers are a way to describe to Eikobot how something should be deployed.
"""
from dataclasses import dataclass

from .compiler.definitions.base_types import EikoResource


@dataclass
class HandlerContext:
    resource: EikoResource


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

    def __init__(self, res: EikoResource) -> None:
        self.res_instance = res

    def create(self, ctx: HandlerContext) -> None:
        raise EikoCRUDHanlderMethodNotImplemented

    def read(self, ctx: HandlerContext) -> None:
        raise EikoCRUDHanlderMethodNotImplemented

    def update(self, ctx: HandlerContext) -> None:
        raise EikoCRUDHanlderMethodNotImplemented

    def delete(self, ctx: HandlerContext) -> None:
        raise EikoCRUDHanlderMethodNotImplemented
