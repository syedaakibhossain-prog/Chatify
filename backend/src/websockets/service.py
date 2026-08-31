from fastapi import status
import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.chat.ConversessionService import ConversessionService
from src.chat.MessageService import MessageService
from src.websockets.manager import ConnectionManager

from src.websockets.schemas import WebSocketMessage


class WebSocketManager:

    def __init__(
        self,
        manager:ConnectionManager,
        conversession_manager:ConversessionService,
        message_manager:MessageService
    ):

        self.manager = manager
        self.conversession_manager = conversession_manager
        self.message_manager = message_manager

    async def connect_socket(
        self,
        websocket,
        db: AsyncSession,
        conversession_id: uuid.UUID,
        user_id: uuid.UUID,
    ):

        conversession = await self.conversession_manager.get_conversession(
            db,
            conversession_id
        )

        if conversession is None:

            await websocket.close(
                code=1008
            )
            return
        
        is_a_member = await self.conversession_manager.is_member(
            db,
            user_id,
            conversession_id
        )

        if not is_a_member:

            await websocket.close(
                code=1008
            )
            return

        await self.manager.connect(
            str(conversession_id),
            websocket
        )

    async def handel_message(
        self,
        db: AsyncSession,
        conversession_id,
        user_id: uuid.UUID,
        message:WebSocketMessage
    ):

        if message.type != "message":
            raise ValueError(
                f"unsopported message type: {message.type}"
            )
        
        print(f"[WS] Saving message: {message.content!r}")

        created_message = await self.message_manager.send_message(
            db=db,
            message_data=message,
            conversession_id=conversession_id,
            sender_id=user_id
        )

        # print(f"[WS] Message saved id={created_message.id}")

        payload = {
            "type":"message",
            "data": {
                "id":str(created_message.id),
                "conversession_id": str(
                    created_message.conversession_id
                ),
                "sender_id": str(created_message.sender_id),
                "content":created_message.content,
                "created_at":(
                    created_message.created_at.isoformat()
                    if created_message.created_at
                    else None
                ),
            },
        }

        room_key = str(conversession_id)
        connections = self.manager.active_connections.get(room_key, set())
        print(f"[WS] Broadcasting to room={room_key!r}, connections={len(connections)}")

        await self.manager.broadcast(
            room_key,
            payload
        )

        # print(f"[WS] Broadcast complete")

    def websocket_disconnect(
        self,
        conversession_id: uuid.UUID,
        websocket
    ):

        self.manager.diconnect(
            str(conversession_id),
            websocket
        )