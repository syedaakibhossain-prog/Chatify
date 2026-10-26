import uuid
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Request, status
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
    request:Request,
    db:Dbsession,
    access_token: str | None = Cookie(
        default=None
    )
) -> User | None:
    """
    FastAPI dependency that resolves the current user from the 'access_token' cookie
    and attaches it to request.state.user for optional access later in the request cycle.

    Parameters:
      request (Request)          : The incoming FastAPI request object.
      db (AsyncSession)          : Injected database session.
      access_token (str | None)  : The JWT access token read from the HTTP-only cookie.

    Returns:
      User | None: The authenticated User ORM object, or None if authentication fails.
    """

    user = await resolve_user_from_token(
        db,
        access_token
    )
    request.state.user = user
    return user


async def resolve_user_from_token(
    db:AsyncSession,
    access_token:str | None
) -> User:
    """
    Resolves and returns a User from a JWT access token string.

    Steps performed:
      1. Raises HTTP 401 if access_token is missing.
      2. Decodes and verifies the JWT; raises 401 if invalid or expired.
      3. Extracts the 'sub' (user ID) claim from the token payload.
      4. Parses the user ID string into a UUID; raises 401 if malformed.
      5. Looks up the User in the database by UUID; raises 401 if not found.

    Parameters:
      db (AsyncSession)         : The async database session for the DB lookup.
      access_token (str | None) : The raw JWT access token string.

    Returns:
      User: The authenticated User ORM object.

    Raises:
      HTTPException (401): If the token is missing, invalid, expired, or the user no longer exists.
    """

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ACCESS TOKEN DOES NOT PROVIDED"
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
