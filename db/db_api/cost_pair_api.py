import datetime
import decimal
import typing

from sqlalchemy import future, update, delete

from db.db_api import session as db_session
from db.models import base

import config as conf


class CostPairApi:
    model = base.CostPair

    @classmethod
    async def _get(cls, pair: str = "", all_: bool = False):
        async with db_session.external_postgres(echo_queries=False) as session_cls:
            async with session_cls() as session:
                stmt = future.select(cls.model)
                if not all_:
                    stmt = stmt.where(
                        cls.model.pair == pair
                    )
                res = await session.execute(stmt)
                return res.scalars().all() if all_ else res.scalar()

    @classmethod
    async def retrieve_cost(cls, pair: str):
        from_, to = pair.split(",")

        def is_expire(updated_at):
            time_exp = updated_at + datetime.timedelta(seconds=conf.TIME_EXPIRE_COST_PAIR)
            return time_exp < datetime.datetime.utcnow()

        pair_ = from_ + to
        res = await cls._get(pair_)
        if res:
            if not is_expire(res.updated_at):
                return res.cost, False
        else:
            pair_ = to + from_
            res = await cls._get(pair_)
            if res:
                if not is_expire(res.updated_at):
                    return res.cost, True

    @classmethod
    async def create(cls, pair: str, cost: decimal.Decimal):
        # create or update
        async with db_session.external_postgres(echo_queries=False) as session_cls:
            async with session_cls() as session:
                stmt = update(cls.model).values(
                    cost=cost, updated_at=datetime.datetime.utcnow()
                ).where(
                    cls.model.pair == pair
                ).returning(cls.model.pair)
                res = await session.execute(stmt)
                res = res.scalar() if res else None
                if not res:
                    stmt = cls.model(pair=pair, cost=cost)
                    session.add(stmt)
                await session.commit()

    @classmethod
    async def delete_(cls, pair: str = "", all_: bool = False):
        async with db_session.external_postgres(echo_queries=False) as session_cls:
            async with session_cls() as session:
                if pair and not all_:
                    stmt = delete(cls.model).where(cls.model.pair == pair)
                if all_:
                    stmt = delete(cls.model)
                await session.execute(stmt)
                await session.commit()
