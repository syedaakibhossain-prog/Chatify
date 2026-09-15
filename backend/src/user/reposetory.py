from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.model import User
from src.user.schemas import UserSearchResults
from starlette import status


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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="USER NOT FOUND"
            )

        return UserSearchResults(
            id=res.id,
            username=res.username,
            last_seen=res.last_seen
        )
