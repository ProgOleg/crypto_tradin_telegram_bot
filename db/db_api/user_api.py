from db.db_api import session as db_session
from db.models import base

from sqlalchemy import future


class UserAPI:
    model = base.User

    @classmethod
    async def create_user_if_necessary(
            cls,
            chat_id: int,
            language: str,
            username: str,
            cr_date=None
    ):
        async with db_session.external_postgres() as session_cls:
            async with session_cls() as session:
                user_exists = await session.execute(
                    future.select(cls.model).where(
                        cls.model.chat_id == chat_id
                    )
                )
                user = user_exists.scalar()
                if not user:
                    user = cls.model(
                        **{"registration_date": cr_date} if cr_date else {},
                        chat_id=chat_id,
                        language=language,
                        username=username
                    )
                    session.add(user)
                    await session.commit()
                    await session.refresh(user)
                    user = user
                return user

    @classmethod
    async def retrieve(
        cls,
        user_id: int,
    ):
        async with db_session.external_postgres() as session_cls:
            async with session_cls() as session:

                user_data = await session.execute(
                    future.select(cls.model).where(
                        cls.model.chat_id == user_id
                    )
                )
                user_data = user_data.scalar()
                assert user_data
                return user_data
