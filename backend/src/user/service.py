import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.cache.cache import CacheService
from src.user.reposetory import UserRepo
from src.user.schemas import UserResults, UserSearchResults

logger = logging.getLogger(__name__)


class UserService:
    """
    Service layer for user lookup operations.

    Wraps UserRepo database calls with HTTP error handling so routes
    receive clean exceptions when users are not found.
    """

    def __init__(
        self,
        repo: UserRepo,
        cache_ser:CacheService
    ) -> None:
        """
        Initializes UserService with a user repository.

        Parameters:
          repo (UserRepo): The repository used for all user database lookups.
        """
        self.repo = repo
        self.cache_ser = cache_ser

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
        user_id:uuid.UUID,
    ) -> UserResults | None:
        cache_key = f"user{user_id}"
        try:
            chached_user = await self.cache_ser._get(
                key=cache_key
            )
        except Exception:
            logger.warning("cached read failled" , exc_info=True)
            chached_user = None

        if not chached_user:
            try:
                res = await self.repo.get_user_by_id(
                    db,
                    user_id,
                    cache_key
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
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("fun_search_user_by_id failed")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error"
                ) from e

        return UserResults(
            id=chached_user.id,
            username=chached_user.username
        )
