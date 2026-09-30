import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.model import User
from src.user.schemas import UserResults, UserSearchResults


class UserRepo:

    async def get_user_by_name(
        self,
        db: AsyncSession,
        username:str
    ) -> UserSearchResults | None:

        query = await db.execute(
            select(User).where(
                User.username == username
            )
        )
        res = query.scalar_one_or_none()
        if res is None:
            return None

        return UserSearchResults(
            id=res.id,
            username=res.username,
            last_seen=res.last_seen
        )
    async def get_user_by_id(
        self,
        db:AsyncSession,
        user_id:uuid.UUID
    ) ->UserResults | None:

        query = await db.execute(
            select(User).where(
                User.id == user_id
            )
        )

        res = query.scalar_one_or_none()
        if res is None:
            return None

        return UserResults(
            id=res.id,
            username=res.username
        )
