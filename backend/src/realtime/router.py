from typing import Annotated, TypeAlias

from fastapi import APIRouter, Cookie, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from src.converseation.reposetory import ConversetionRepo
from src.converseation.service import ConversationService
from src.database import get_db
from src.message.reposetory import MessageRepo
from src.message.service import MessageService
from src.realtime.auth import websocket_auth
from src.realtime.handler import RealTimeHandler
from src.realtime.manager import manager
from src.realtime.schemas import outbound
from src.user.reposetory import UserRepo
from src.user.service import UserService

DbSession: TypeAlias = Annotated[AsyncSession, Depends(get_db)]
AccessToken: TypeAlias = Annotated[str | None, Cookie()]


# ---- Service factories ----

def get_user_service() -> UserService:
    return UserService(UserRepo())


UserServiceDep: TypeAlias = Annotated[UserService, Depends(get_user_service)]


def get_conversation_service(
    user_ser: UserServiceDep,
) -> ConversationService:
    return ConversationService(ConversetionRepo(), user_ser)


ConversationServiceDep: TypeAlias = Annotated[
    ConversationService, Depends(get_conversation_service)
]

def _get_message_service() -> MessageService :
    msg_repo = MessageRepo()

    return MessageService(
        msg_repo
    )

MessageServiceDep : TypeAlias = Annotated[MessageService , Depends(_get_message_service)]



# ---- WS endpoint ----

router = APIRouter(
    prefix="/realtime",
    tags=["Realtime"]
)


@router.websocket("/ws")
async def websocket_endpoint(
    ws: WebSocket,
    db: DbSession,
    access_token: AccessToken,
    conversation_service: ConversationServiceDep,
    message_service : MessageServiceDep,
) -> None:
    # 1. Authenticate BEFORE accept
    user = await websocket_auth(db, ws, access_token)
    if user is None:
        return  # websocket_auth already closed the socket

    # 2. Accept
    await ws.accept()

    # 3. Register + join rooms
    await manager.connect(user.id, ws)

    conversation_ids = await conversation_service.get_conversation_ids_for_user(
        db=db,
        user_id=user.id,
    )
    await manager.join_conversation(user.id, conversation_ids or [])

    # 4. Greeting
    await ws.send_json(outbound(
        "ready",
        user_id=str(user.id),
        conversations=[str(cid) for cid in (conversation_ids or [])],
    ))

    # 5. Main loop
    handler = RealTimeHandler(
        ws,
        conversation_service,
        message_service,
        db,
        user
    )

    try:
        while True:
            data = await ws.receive_json()

            if data.get("type") == "ping":
                await ws.send_json(outbound("pong"))
                continue

            try:
                await handler.despatch(data)
            except Exception as exc:
                import logging
                logging.getLogger(__name__).exception("WS handler error")
                await ws.send_json(outbound("error", detail=str(exc)))

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(user.id, ws)
