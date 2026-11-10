from typing import Annotated, TypeAlias

from fastapi import Cookie, HTTPException, WebSocket, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.dependences import resolve_user_from_token
from src.model import User

AccessToken : TypeAlias = Annotated[str | None , Cookie()]

async def websocket_auth(
    db : AsyncSession,
    ws : WebSocket,
    access_token : AccessToken
) -> User | None :
    """
    Authenticates a WebSocket connection before accepting it.

    Attempts to resolve the user from the access_token cookie. If authentication
    fails (token missing, invalid, or user not found), the socket is accepted and
    immediately closed with a 1008 Policy Violation code, and None is returned.
    The caller must check for None and stop further processing.

    Parameters:
      db (AsyncSession)         : The async database session for the user lookup.
      ws (WebSocket)            : The WebSocket connection to authenticate.
      access_token (AccessToken): The JWT access token cookie value (may be None).

    Returns:
      User | None: The authenticated User ORM object if successful, or None if
                   authentication failed (socket is already closed in that case).
    """

    try:
        user = await resolve_user_from_token(
            db,
            access_token
        )
    except HTTPException:
        await ws.accept()
        await ws.close(status.WS_1008_POLICY_VIOLATION)
        return None

    if user is None :
        await ws.accept()
        await ws.close(status.WS_1008_POLICY_VIOLATION)
        return None

    return user
