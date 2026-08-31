import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.model import User


class UserRepository:

    async def get_user_by_email(
        self,
        db: AsyncSession,
        email: str,
    ) -> User | None:

        result = await db.execute(
            select(User).where(
                User.email == email
            )
        )

        return result.scalar_one_or_none()

    async def get_user_by_id(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> User | None:

        result = await db.execute(
            select(User).where(
                User.id == user_id
            )
        )

        return result.scalar_one_or_none()

    async def get_user_by_name(
        self,
        db: AsyncSession,
        username: str,
    ) -> User | None:

        result = await db.execute(
            select(User).where(
                User.username == username
            )
        )

        return result.scalar_one_or_none()

    async def create_user(
        self,
        db: AsyncSession,
        user: User,
    ) -> User:

        db.add(user)

        await db.commit()

        await db.refresh(user)

        return user