import uuid
from typing import Any

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from src.converseation.service import ConversationService
from src.message.service import MessageService
from src.model import User
from src.realtime.manager import manager
from src.realtime.schemas import outbound


class RealTimeHandler :
    def __init__(
        self,
        ws : WebSocket,
        conversation_service : ConversationService,
        message_service : MessageService,
        db : AsyncSession,
        user : User
    ) -> None :

        self.ws = ws
        self.user = user
        self.conversation_service = conversation_service
        self.message_service = message_service
        self.db = db

    async def despatch(
        self,
        data : dict[str , Any]
    ) -> None :
        event_type = data.get("type")

        # Bug 1 fix: guard against missing "type" key
        if event_type is None:
            await self.ws.send_json(outbound("error", detail="Missing event type"))
            return

        handler = getattr(self, f"on_{event_type.replace(':', '_')}", None)
        if handler is None:
            await self.ws.send_json(outbound("error", detail=f"Unknown event: {event_type}"))
            return
        await handler(data)

    # ---- helpers ----

    async def _parse_conversation_id(
        self,
        data: dict[str, Any],
    ) -> uuid.UUID | None:
        """Safely extract and parse conversation_id, sending an error on failure."""
        raw = data.get("conversation_id")
        if raw is None:
            await self.ws.send_json(outbound("error", detail="Missing conversation_id"))
            return None
        try:
            return uuid.UUID(raw)
        except (ValueError, AttributeError):
            await self.ws.send_json(outbound("error", detail="Invalid conversation_id"))
            return None

    # ---- Handlers ----

    async def on_message_send(
        self,
        data : dict[str , Any]
    ) -> None :

        conversation_id = await self._parse_conversation_id(data)
        if conversation_id is None:
            return

        content = data.get("content" , "").strip()
        temp_id = data.get("temp_id")

        if not content or len(content) > 1000:
            await self.ws.send_json(outbound("error", detail="Invalid content"))
            return

        is_member = await self.conversation_service.is_member(
            db = self.db,
            conversation_id = conversation_id,
            user_id= self.user.id
        )
        if not is_member:
               await self.ws.send_json(outbound("error", detail="Not a member"))
               return

        message = await self.message_service.create_message(
            db=self.db,
            conversation_id=conversation_id,
            sender_id=self.user.id,
            content=content,
        )
        serialized = self._serialize(message)

        await manager.send_to_user(
             self.user.id,
             outbound("message:ack", temp_id=temp_id, message=serialized),
        )
        await manager.broadcast_to_conversation(
               conversation_id=conversation_id,
               payload=outbound("message:new", message=serialized),
               user_id=self.user.id,
        )

    async def on_typing_start(
        self,
        data : dict[str , Any]
    ) -> None :

        conversation_id = await self._parse_conversation_id(data)
        if conversation_id is None:
            return

        is_member = await self.conversation_service.is_member(
            db = self.db,
            conversation_id = conversation_id,
            user_id= self.user.id
        )
        if not is_member:
               return

        await manager.broadcast_to_conversation(
            conversation_id=conversation_id,
            payload=outbound(
                "typing:update",
                conversation_id = str(conversation_id),
                user_id = str(self.user.id),
                username = self.user.username,
                is_typing = True
            ),
            user_id=self.user.id
        )

    async def on_typing_stop(
        self,
        data : dict[str , Any]
    ) -> None :

        conversation_id = await self._parse_conversation_id(data)
        if conversation_id is None:
            return

        # Bug 2 fix: add membership check (was missing unlike on_typing_start)
        is_member = await self.conversation_service.is_member(
            db = self.db,
            conversation_id = conversation_id,
            user_id= self.user.id
        )
        if not is_member:
               return

        await manager.broadcast_to_conversation(
            conversation_id=conversation_id,
            payload=outbound(
                "typing:update",
                conversation_id = str(conversation_id),
                user_id = str(self.user.id),
                username = self.user.username,
                is_typing = False
            ),
            user_id=self.user.id
        )

    async def on_message_read(
        self,
        data : dict[str , Any]
    ) -> None :
        conversation_id = await self._parse_conversation_id(data)
        if conversation_id is None:
            return

        await self.conversation_service.mark_conversation_read(
            db=self.db,
            conversation_id=conversation_id,
            user_id=self.user.id
        )
        await manager.broadcast_to_conversation(
            conversation_id=conversation_id,
            payload=outbound(
                "read:update",
                conversation_id = str(conversation_id),
                user_id = str(self.user.id)
            ),
            user_id= self.user.id
        )



    @staticmethod
    def _serialize(message) -> dict:
        return {
            "id": str(message.id),
            "conversation_id": str(message.conversation_id),
            "sender_id": str(message.sender_id),
            "content": message.content,
            "message_type": message.message_type,
            "created_at": message.created_at.isoformat(),
            "is_deleted": message.is_deleted,
        }
