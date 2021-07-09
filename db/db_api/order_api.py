import datetime
from typing import Optional
import config
from db.db_api import session as db_session
from db.models import base

from sqlalchemy import future
from sqlalchemy import update

from utils import helpers


class OrderAPI:
    MODEL = base.Order

    @classmethod
    async def base_executor_get(cls, stmt):
        async with db_session.external_postgres() as session_cls:
            async with session_cls() as session:
                res = await session.execute(stmt)
                return res.scalar()

    @classmethod
    async def create_order(cls, data: dict):
        async with db_session.external_postgres() as session_cls:
            async with session_cls() as session:
                stmt = cls.MODEL(**data)
                session.add(stmt)
                await session.commit()
                await session.refresh(stmt)
                return stmt.id

    @classmethod
    async def get_last(cls, user_id: int):
        async with db_session.external_postgres() as session_cls:
            async with session_cls() as session:
                expected_date = datetime.datetime.utcnow() - datetime.timedelta(minutes=config.T_EXPIRE)
                stmt = future.select(cls.MODEL).where(
                    cls.MODEL.user_id == user_id,
                    cls.MODEL.cr_date >= expected_date
                )
                res = await session.execute(stmt)
                return res.scalar()

    @classmethod
    async def set_approve(cls, pk: int):
        async with db_session.external_postgres() as session_cls:
            async with session_cls() as session:
                res = await session.execute(
                    update(cls.MODEL).where(
                        cls.MODEL.id == pk
                    ).values(
                        approve=True,
                        approved_date=datetime.datetime.utcnow()
                    )
                )

    @classmethod
    async def checking_expiration(cls, order_id: str):
        # return True if order expire
        stmt = future.select(cls.MODEL).where(cls.MODEL.id == int(order_id))
        res = await cls.base_executor_get(stmt)
        expiration_date = res.cr_date + datetime.timedelta(minutes=config.T_EXPIRE)
        is_expired = datetime.datetime.utcnow() > expiration_date
        expired_time = helpers.format_delta(datetime.datetime.utcnow() - expiration_date) if is_expired else None
        return is_expired, res, expired_time

    @classmethod
    async def update(cls, data, pk: Optional[int] = None):
        async with db_session.external_postgres() as session_cls:
            async with session_cls() as session:
                stmt = update(cls.MODEL).values(**data).where(cls.MODEL.id == pk)
                await session.execute(stmt)

    @classmethod
    async def set_success(cls, pk: int):
        await cls.update(
            {
                "success": True,
                "success_date": datetime.datetime.utcnow()
            },
            pk
        )

    @classmethod
    async def retrieve(
        cls,
        order_id: int,
    ) -> MODEL:
        async with db_session.external_postgres() as session_cls:
            async with session_cls() as session:
                order_data = await session.execute(
                    future.select(cls.MODEL).where(
                        cls.MODEL.id == order_id
                    )
                )
                order_data = order_data.scalar()
                assert order_data
                return order_data

