import asyncio
import time
from datetime import datetime
from typing import Optional

from eikobot.core.handlers import AsyncCRUDHandler, CRUDHandler, HandlerContext


class BotHandler(AsyncCRUDHandler):
    resource = "BotRes"

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
    resource = "TopRes"

    def __init__(self) -> None:
        self.created: Optional[datetime] = None

    def create(self, ctx: HandlerContext) -> None:
        self.created = datetime.utcnow()
        time.sleep(1)
        ctx.deployed = True

    def read(self, ctx: HandlerContext) -> None:
        if self.created is not None:
            ctx.deployed = True

        ctx.changes["time"] = datetime.utcnow()

    def update(self, ctx: HandlerContext) -> None:
        self.created = ctx.changes.get("time")
        if self.created is not None:
            ctx.updated = True
