"""
This file is purely used for testing purposes.
"""
from eikobot.core.handlers import CRUDHandler, HandlerContext
from eikobot.core.helpers import EikoPromise


class PromiseTestHandler1(CRUDHandler):
    """
    The PromiseTest_1 resource has a promise to fulfill.
    """

    __eiko_resource__ = "PromiseTest_1"

    async def create(self, ctx: HandlerContext) -> None:
        ctx.raw_resource.promises[0].set("passed promise")
        ctx.deployed = True


class PromiseTestHandler2(CRUDHandler):
    """
    The PromiseTest_2 resource has a it needs to wait for.
    """

    __eiko_resource__ = "PromiseTest_2"

    async def create(self, ctx: HandlerContext) -> None:
        ctx.deployed = True
        assert isinstance(ctx.resource, dict)
        assert not isinstance(ctx.resource["prop_2"], EikoPromise)
