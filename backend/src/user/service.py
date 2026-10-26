import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.user.reposetory import UserRepo
from src.user.schemas import UserResults, UserSearchResults


class UserService:
    """
    Service layer for user lookup operations.

    Wraps UserRepo database calls with HTTP error handling so routes
    receive clean exceptions when users are not found.
    """

    def __init__(
        self,
        repo: UserRepo
    ) -> None:
        """
        Initializes UserService with a user repository.

        Parameters:
          repo (UserRepo): The repository used for all user database lookups.
        """
        self.repo = repo

    # @dec:search user by username
    # @parameter: db
    # @parameter: username
    # @return: UserSearchResults
    async def fun_search_user(
        self,
        db:AsyncSession,
        username:str
    ) -> UserSearchResults | None:

        user = await self.repo.get_user_by_name(
            db,
            username
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="USER NOT FOUND"
            )

        return UserSearchResults(
            id=user.id,
            username=user.username,
            last_seen=user.last_seen
        )

    # @dec:search user by user id
    # @parameter: db
    # @parameter: user_id
    # @return: UserResults
    async def fun_search_user_by_id(
        self,
        db:AsyncSession,
        user_id:uuid.UUID
    ) -> UserResults | None:

        res = await self.repo.get_user_by_id(
            db,
            user_id
        )

        if res is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="USER NOT FOUND"
            )

        return UserResults(
            id=res.id,
            username=res.username
        )
