"""
This file is purely used for testing purposes.
"""
from eikobot.core.handlers import Handler, HandlerContext
from eikobot.core.helpers import EikoPromise, EikoBaseModel


class PromiseTestHandler1(Handler):
    """
    The PromiseTest_1 resource has a promise to fulfill.
    """

    __eiko_resource__ = "PromiseTest_1"

    async def execute(self, ctx: HandlerContext) -> None:
        promise = ctx.raw_resource.promises.get("prop_2")
        if promise is not None:
            promise.set("passed promise")
            ctx.deployed = True


class PromiseTest2(EikoBaseModel):
    __eiko_resource__ = "PromiseTest_2"

    prop_1: str
    prop_2: str


class PromiseTestHandler2(Handler):
    """
    The PromiseTest_2 resource has a it needs to wait for.
    """

    __eiko_resource__ = "PromiseTest_2"

    async def execute(self, ctx: HandlerContext) -> None:
        ctx.deployed = True
        if not isinstance(ctx.resource, PromiseTest2):
            raise Exception
        if isinstance(ctx.resource.prop_2, EikoPromise):
            raise Exception
        if isinstance(ctx.raw_resource.properties.get("prop_2"), EikoPromise):
            raise Exception
