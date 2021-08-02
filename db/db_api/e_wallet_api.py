from sqlalchemy import future

from db.db_api import session as db_session
from db.models import base


class EWalletsApi:
    models = base.EWallets

    @classmethod
    async def get(cls, identifier: str):
        async with db_session.external_postgres(echo_queries=False) as session_cls:
            async with session_cls() as session:
                res = await session.execute(future.select(cls.models).where(cls.models.identifier == identifier))
                return res.scalar()


