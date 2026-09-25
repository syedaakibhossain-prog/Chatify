from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.dependences import resolve_user_from_token
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
    user_service: user_service,
    access_token: str | None = Cookie(default=None),
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

    # Exclude the currently logged-in user from results
    if access_token:
        try:
            current_user = await resolve_user_from_token(db, access_token)
            if current_user and current_user.id == user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="USER NOT FOUND"
                )
        except HTTPException as e:
            if e.status_code != status.HTTP_404_NOT_FOUND:
                raise

    return UserSearchResults(
        id=user.id,
        username=user.username,
        last_seen=user.last_seen
    )
