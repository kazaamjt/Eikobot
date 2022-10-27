# pylint: disable=no-self-use
"""
Handlers are a way to describe to Eikobot how something should be deployed.
"""
from dataclasses import dataclass

from ..compiler.definitions.base_types import EikoResource


@dataclass
class HandlerContext:
    resource: EikoResource


class EikoCRUDHanlderMethodNotImplemented(Exception):
    """Raised if a method is not implemented."""


class CRUDHandler:
    """
    A crud resource handler implements python code that handles
    the deployment and updating of resources in python code.
    """

    resource: str

    def create(self, ctx: HandlerContext) -> None:
        raise EikoCRUDHanlderMethodNotImplemented

    def read(self, ctx: HandlerContext) -> None:
        raise EikoCRUDHanlderMethodNotImplemented

    def update(self, ctx: HandlerContext) -> None:
        raise EikoCRUDHanlderMethodNotImplemented

    def delete(self, ctx: HandlerContext) -> None:
        raise EikoCRUDHanlderMethodNotImplemented
