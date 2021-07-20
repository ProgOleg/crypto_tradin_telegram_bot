import typing
import sys

sys.path = ["", ".."] + sys.path

import asyncio

from sqlalchemy.ext import asyncio as sa_asyncio

import wallets
from db import models
from db.db_api import session as db_session


async def populate_wallets(session):
    model = models.base.EWallets
    _temp = []
    for identifier, val in wallets.WALLETS.items():
        _temp.append(
            model(
                identifier=identifier,
                wallet=val["wallet"],
                memo=val["memo"],
                description=val["description"]
            )
        )
    await session.commit()


async def populate(session_cls: typing.ClassVar[sa_asyncio.AsyncSession]):
    async with session_cls() as session:
        await populate_wallets(session)


async def main():
    async with db_session.external_postgres() as session_cls:
        await populate(session_cls)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    print("Database is successfully populated!", end="***" * 50)
