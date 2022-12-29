"""
A module to tests the deployment of resources
"""
from eikobot.core.handlers import CRUDHandler, HandlerContext


class BaseHandler(CRUDHandler):
    """
    Handles the deployment of BaseResources.
    """

    resource = "BaseResource"

    def __init__(self) -> None:
        self.created = False
        self.updated = False
        self.create_called = 0
        self.update_called = 0

    async def create(self, ctx: HandlerContext) -> None:
        self.created = True
        self.create_called += 1
        ctx.deployed = True


class MidHandler(CRUDHandler):
    """
    Handles the deployment of MidResources.
    """

    resource = "MidResource"

    def __init__(self) -> None:
        self.created = False
        self.updated = False
        self.create_called = 0
        self.update_called = 0

    async def create(self, ctx: HandlerContext) -> None:
        self.created = True
        self.create_called += 1
        ctx.deployed = True

    async def read(self, ctx: HandlerContext) -> None:
        if self.created:
            ctx.deployed = True


class TopHandler(CRUDHandler):
    """
    Handles the deployment of TopResource.
    """

    resource = "TopResource"

    def __init__(self) -> None:
        self.created = False
        self.updated = False
        self.create_called = 0
        self.update_called = 0

    async def create(self, ctx: HandlerContext) -> None:
        self.created = True
        self.create_called += 1
        ctx.deployed = True

    async def read(self, ctx: HandlerContext) -> None:
        if self.created:
            ctx.deployed = True

        if not self.updated:
            ctx.changes["updated"] = False

    async def update(self, ctx: HandlerContext) -> None:
        if ctx.changes.get("updated") is None:
            raise Exception("Well this test failed...")

        ctx.deployed = True
        self.updated = True
        self.update_called += 1
