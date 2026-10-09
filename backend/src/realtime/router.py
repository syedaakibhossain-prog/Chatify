import asyncio
import logging
import time
from contextlib import suppress
from typing import Annotated, TypeAlias

from fastapi import APIRouter, Cookie, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.authentication.utiles import verify_access_token
from src.config import settings
from src.converseation.reposetory import ConversetionRepo
from src.converseation.service import ConversationService
from src.database import SessionLocal, get_db
from src.message.reposetory import MessageRepo
from src.message.service import MessageService
from src.realtime.auth import websocket_auth
from src.realtime.handler import RealTimeHandler
from src.realtime.manager import manager
from src.realtime.schemas import outbound
from src.user.reposetory import UserRepo
from src.user.service import UserService

logger = logging.getLogger(__name__)

DbSession: TypeAlias = Annotated[AsyncSession, Depends(get_db)]
AccessToken: TypeAlias = Annotated[str | None, Cookie()]


def get_user_service() -> UserService:
    return UserService(UserRepo())


UserServiceDep: TypeAlias = Annotated[UserService, Depends(get_user_service)]


def get_conversation_service(user_ser: UserServiceDep) -> ConversationService:
    return ConversationService(ConversetionRepo(), user_ser)


ConversationServiceDep: TypeAlias = Annotated[
    ConversationService, Depends(get_conversation_service)
]


def _get_message_service(conn_ser: ConversationServiceDep) -> MessageService:
    return MessageService(MessageRepo(), conn_ser)


MessageServiceDep: TypeAlias = Annotated[MessageService, Depends(_get_message_service)]


router = APIRouter(prefix="/v1/realtime", tags=["Realtime"])


@router.websocket("/ws")
async def websocket_endpoint(
    ws: WebSocket,
    db: DbSession,
    access_token: AccessToken,
    conversation_service: ConversationServiceDep,
    message_service: MessageServiceDep,
) -> None:
    # 1. Authenticate BEFORE accept
    origin = ws.headers.get("origin")
    if origin not in settings.allowed_origins_list:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    if not access_token:
        await ws.close(code=4401)
        return

    payload = verify_access_token(access_token)
    if payload is None:
        await ws.close(code=4401)
        return
    token_exp = int(payload["exp"])

    user = await websocket_auth(db, ws, access_token)
    if user is None:
        return



    conversation_ids = await conversation_service.get_conversation_ids_for_user(
        db=db,
        user_id=user.id,
    )
    with suppress(Exception):
        await db.close()


    await ws.accept()
    await manager.connect(user.id, ws)
    await manager.join_conversation(user.id, conversation_ids or [])

    # 4. Greeting
    await ws.send_json(
        outbound(
            "ready",
            user_id=str(user.id),
            conversations=[str(cid) for cid in (conversation_ids or [])],
        )
    )

    try:
        async with SessionLocal() as db2:
            handler = RealTimeHandler(
                ws, conversation_service, message_service, db2, user
            )

            while True:
                try:
                    data = await asyncio.wait_for(ws.receive_json(), timeout=30)
                except asyncio.TimeoutError:
                    if time.time() >= token_exp:
                        await ws.send_json(outbound("auth:expired"))
                        await ws.close(code=4401)
                        break
                    await ws.send_json(outbound("pong"))
                    continue

                if time.time() >= token_exp:
                    await ws.send_json(outbound("auth:expired"))
                    await ws.close(code=4401)
                    break

                if data.get("type") == "ping":
                    await ws.send_json(outbound("pong"))
                    continue

                try:
                    await handler.despatch(data)
                except Exception as exc:
                    logger.exception("WS handler error")
                    await ws.send_json(outbound("error", detail=str(exc)))

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(user.id, ws)
