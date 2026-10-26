import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.model import User
from src.user.schemas import UserResults, UserSearchResults


class UserRepo:
    """
    Data access layer for looking up User records in the user module.

    Returns schema objects (UserSearchResults, UserResults) rather than raw ORM
    models, providing a clean separation between the database layer and the service layer.
    """

    async def get_user_by_name(
        self,
        db: AsyncSession,
        username:str
    ) -> UserSearchResults | None:
        """
        Looks up a user by their exact username and returns a lightweight search result.

        Parameters:
          db (AsyncSession): The async database session.
          username (str)   : The exact username to search for.

        Returns:
          UserSearchResults | None: A schema with id, username, and last_seen,
                                    or None if no user with that username exists.
        """

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
        """
        Looks up a user by their UUID and returns a minimal result schema.

        Parameters:
          db (AsyncSession)  : The async database session.
          user_id (uuid.UUID): The UUID of the user to look up.

        Returns:
          UserResults | None: A schema with id and username, or None if not found.
        """

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
