import uuid
from typing import Annotated

from fastapi import (
    Cookie,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from src.authentication.reposetory import (
    UserRepository,
)
from src.authentication.utiles import (
    verify_access_token,
)
from src.database import get_db
from src.model import User

Dbsession = Annotated[AsyncSession , Depends(get_db)]




async def get_user(
    db:Dbsession,
    access_token: str | None = Cookie(
        default=None
    )
) -> User | None:

    return await resolve_user_from_token(
        db,
        access_token
    )


async def resolve_user_from_token(
    db:AsyncSession,
    access_token:str | None
) -> User:

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ACCESS TOKEN DOES NOT PROVIEDED"
        )

    payload = verify_access_token(
        access_token
    )

    if not payload:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    user_id = payload.get("sub")

    if not user_id:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    try:
        user_uuid = uuid.UUID(user_id)

    except (ValueError, AttributeError):

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier",
        )

    user_repository = UserRepository()

    user = await user_repository.get_user_by_id(
        db,
        user_uuid,
    )

    if not user:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )

    return user
