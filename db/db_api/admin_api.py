import config
from db.db_api import session as db_session
from db.models import base

from sqlalchemy import future
from sqlalchemy import update


class AdminApi:
    models = base.Admins

    @classmethod
    async def get_admin(cls):
        async with db_session.external_postgres(echo_queries=False) as session_cls:
            async with session_cls() as session:
                res = await session.execute(future.select(cls.models).where(cls.models.is_active == True))
                return res.scalars().all()


