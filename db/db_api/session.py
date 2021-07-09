import contextlib
import os

from sqlalchemy import orm
from sqlalchemy.ext import asyncio as sa_asyncio
import config


@contextlib.asynccontextmanager
async def external_postgres(
    echo_queries: bool = False,
):
    # async_pg = pgsql_connection_url.replace("postgresql+psycopg2", "postgresql+asyncpg")
    async_pg = config.PG_URL
    engine = sa_asyncio.create_async_engine(async_pg, echo=echo_queries)
    async_session_cls = orm.sessionmaker(bind=engine, class_=sa_asyncio.AsyncSession)
    setattr(async_session_cls, "_asyncpg_connection_host", async_pg)
    yield async_session_cls
