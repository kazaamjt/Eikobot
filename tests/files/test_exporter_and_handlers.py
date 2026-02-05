"""
This file is purely used for testing purposes.
"""

import asyncio
import time
from datetime import datetime

from eikobot.core.handlers import CRUDHandler, HandlerContext


class BotHandler(CRUDHandler):
    """
    The BotRes or bottom resource should not depend on anything.
    It should be a base tasks.
    """

    __eiko_resource__ = "BotRes"

    def __init__(self) -> None:
        self.created = False

    async def create(self, ctx: HandlerContext) -> None:
        self.created = True
        await asyncio.sleep(1)
        ctx.deployed = True

    async def read(self, ctx: HandlerContext) -> None:
        if self.created:
            ctx.deployed = True


class TopHandler(CRUDHandler):
    """
    The TopRes depends on MidRes, but MidRes doesn't have
    a handler, so it doesn't need to be added to the task model.
    """

    __eiko_resource__ = "TopRes"

    def __init__(self) -> None:
        self.created: datetime | None = None

    async def create(self, ctx: HandlerContext) -> None:
        self.created = datetime.utcnow()
        time.sleep(1)
        ctx.deployed = True

    async def read(self, ctx: HandlerContext) -> None:
        if self.created is not None:
            ctx.deployed = True

        ctx.changes["time"] = datetime.utcnow()

    async def update(self, ctx: HandlerContext) -> None:
        self.created = ctx.changes.get("time")
        if self.created is not None:
            ctx.updated = True
