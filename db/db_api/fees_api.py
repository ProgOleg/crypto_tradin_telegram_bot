import datetime
import decimal
import typing

from sqlalchemy import future, update, delete

from db.db_api import session as db_session
from db.models import base

import config as conf


class FeesApi:
    model = base.Fees

    @classmethod
    async def _get(cls, coin: str = "", all_: bool = False):
        async with db_session.external_postgres(echo_queries=False) as session_cls:
            async with session_cls() as session:
                stmt = future.select(cls.model)
                if not all_:
                    stmt = stmt.where(
                        cls.model.coin == coin
                    )
                res = await session.execute(stmt)
                return res.scalars().all() if all_ else res.scalar()

    @classmethod
    async def retrieve_fees(cls, coin: str):

        def is_expire(updated_at):
            time_exp = updated_at + datetime.timedelta(seconds=conf.TIME_EXPIRE_FEES)
            return time_exp < datetime.datetime.utcnow()

        res = await cls._get(coin)
        if res:
            if not is_expire(res.updated_at):
                return res.min_deposit, res.fees_type, res.fees_amount

    @classmethod
    async def create(cls, coin: str, data: dict):
        # create or update
        async with db_session.external_postgres(echo_queries=False) as session_cls:
            async with session_cls() as session:
                stmt = update(cls.model).values(**data, **dict(updated_at=datetime.datetime.utcnow(), coin=coin)
                ).where(
                    cls.model.coin == coin
                ).returning(cls.model.coin)
                res = await session.execute(stmt)
                res = res.scalar() if res else None
                if not res:
                    stmt = cls.model(**data, **dict(coin=coin))
                    session.add(stmt)
                await session.commit()

    @classmethod
    async def delete_(cls, coin: str = "", all_: bool = False):
        async with db_session.external_postgres(echo_queries=False) as session_cls:
            async with session_cls() as session:
                if coin and not all_:
                    stmt = delete(cls.model).where(cls.model.coin == coin)
                if all_:
                    stmt = delete(cls.model)
                await session.execute(stmt)
                await session.commit()
