from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
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
    response_model=UserSearchResults
)
async def search_user(
    db:DBsession,
    username:str,
    user_service: user_service
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

    return UserSearchResults(
        id=user.id,
        username=user.username,
        last_seen=user.last_seen
    )
