import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.model import User


class UserRepository:
    """
    Data access layer for User records.

    Provides low-level async database query methods used by AuthService.
    All methods accept an AsyncSession and return ORM User objects or None.
    """

    async def get_user_by_email(
        self,
        db: AsyncSession,
        email: str,
    ) -> User | None:
        """
        Fetches a single User whose email matches the given address.

        Parameters:
          db (AsyncSession): The async database session.
          email (str)      : The email address to look up.

        Returns:
          User | None: The matching User ORM object, or None if not found.
        """

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
        """
        Fetches a single User by their UUID primary key.

        Parameters:
          db (AsyncSession)  : The async database session.
          user_id (uuid.UUID): The UUID of the user to retrieve.

        Returns:
          User | None: The matching User ORM object, or None if not found.
        """

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
        """
        Fetches a single User whose username matches exactly.

        Parameters:
          db (AsyncSession): The async database session.
          username (str)   : The exact username to search for.

        Returns:
          User | None: The matching User ORM object, or None if not found.
        """

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
        """
        Persists a new User object to the database.

        Parameters:
          db (AsyncSession): The async database session.
          user (User)      : The User ORM instance to insert (username, email, hashed_password
                             must already be set).

        Returns:
          User: The same User instance, refreshed with the DB-generated fields (id, last_seen).
        """

        db.add(user)

        await db.commit()

        await db.refresh(user)

        return user