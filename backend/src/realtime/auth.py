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

    try:
        user = await resolve_user_from_token(
            db,
            access_token
        )
    except HTTPException:
        await ws.close(status.WS_1008_POLICY_VIOLATION)
        return None

    if user is None :
        await ws.close(status.WS_1008_POLICY_VIOLATION)
        return None

    return user
