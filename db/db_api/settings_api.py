import config
from db.db_api import session as db_session
from db.models import base

from sqlalchemy import future
from sqlalchemy import update


class SettingsApi:
    models = base.Settings

    @classmethod
    async def get_markup(cls):
        async with db_session.external_postgres(echo_queries=False) as session_cls:
            async with session_cls() as session:
                res = await session.execute(future.select(cls.models))
                res = res.scalar()
                return res.markup if res else 0

