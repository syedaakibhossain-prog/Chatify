from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.dependences import get_user
from src.model import User
from src.redis.ratelimiter import rate_limit
from src.redis.ratelimits import USER_SEARCH
from src.user.reposetory import UserRepo
from src.user.schemas import UserSearchResults
from src.user.service import UserService

router = APIRouter(
    prefix="/user",
    tags=["user"]
)

DBsession = Annotated[AsyncSession , Depends(get_db)]

def get_user_service():
    user_repo = UserRepo()
    return UserService(
        user_repo
    )
user_service = Annotated[UserService , Depends(get_user_service)]

@router.get(
    "/search",
    response_model=UserSearchResults,
    dependencies=[Depends(rate_limit("user:search", USER_SEARCH))],
)
async def search_user(
    db:DBsession,
    username:str,
    user_service: user_service,
    me:Annotated[User, Depends(get_user)]
) -> UserSearchResults | None:
    user = await user_service.fun_search_user(
        db,
        username
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="USER NOT FOUND"
        )

    if user.id == me.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user not found"
        )

    return UserSearchResults(
        id=user.id,
        username=user.username,
        last_seen=user.last_seen
    )
