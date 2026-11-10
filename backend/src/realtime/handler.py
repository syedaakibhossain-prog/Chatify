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
    """
    Handles inbound WebSocket events for a single authenticated user connection.

    Routes incoming JSON messages to the appropriate event handler method
    (on_message_send, on_typing_start, on_typing_stop, on_message_read) based
    on the 'type' field of the incoming payload.
    """
    def __init__(
        self,
        ws : WebSocket,
        conversation_service : ConversationService,
        message_service : MessageService,
        db : AsyncSession,
        user : User
    ) -> None :
        """
        Initializes the handler with all required dependencies.

        Parameters:
          ws (WebSocket)                         : The active WebSocket connection for this user.
          conversation_service (ConversationService): Used to verify conversation membership.
          message_service (MessageService)       : Used to persist and retrieve messages.
          db (AsyncSession)                      : The async database session for this connection.
          user (User)                            : The authenticated User ORM object.
        """

        self.ws = ws
        self.user = user
        self.conversation_service = conversation_service
        self.message_service = message_service
        self.db = db

    #@parameter: data - dict[str , Any]
    async def despatch(
        self,
        data : dict[str , Any]
    ) -> None :
        """
        Routes an incoming WebSocket message to the correct event handler.

        Reads the 'type' field from the data dict (e.g. 'message:send') and
        calls the matching method (e.g. on_message_send). Sends an error back
        if the type is missing or unknown.

        Parameters:
          data (dict[str, Any]): The parsed JSON payload received from the WebSocket.

        Returns:
          None
        """
        event_type = data.get("type")


        if event_type is None:
            await self.ws.send_json(outbound("error", detail="Missing event type"))
            return

        handler = getattr(self, f"on_{event_type.replace(':', '_')}", None)
        if handler is None:
            await self.ws.send_json(outbound("error", detail=f"Unknown event: {event_type}"))
            return
        await handler(data)



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
        """
        Handles a 'message:send' event from the WebSocket client.

        Steps:
          1. Parses the conversation_id from the data.
          2. Validates the message content (non-empty, max 1000 chars).
          3. Verifies the sender is a member of the conversation.
          4. Persists the message via MessageService.
          5. Sends an 'message:ack' confirmation back to the sender.
          6. Broadcasts a 'message:new' event to all OTHER members of the conversation.

        Parameters:
          data (dict[str, Any]): The WebSocket payload. Expected keys:
            - conversation_id (str): UUID of the target conversation.
            - content (str)        : The message text.
            - temp_id (str)        : A client-generated temp ID echoed back in the ack.

        Returns:
          None
        """

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
        """
        Handles a 'typing:start' event — notifies other conversation members that this
        user has started typing.

        Parameters:
          data (dict[str, Any]): WebSocket payload. Expected key:
            - conversation_id (str): UUID of the conversation where the user is typing.

        Returns:
          None
        """

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
        """
        Handles a 'typing:stop' event — notifies other conversation members that this
        user has stopped typing.

        Parameters:
          data (dict[str, Any]): WebSocket payload. Expected key:
            - conversation_id (str): UUID of the conversation where the user stopped typing.

        Returns:
          None
        """

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

    async def _require_member(
        self,
        conversation_id:uuid.UUID
    ) -> bool:
        """
        Verifies the current user is a member of a conversation, sending an error if not.

        Parameters:
          conversation_id (uuid.UUID): The UUID of the conversation to check.

        Returns:
          bool: True if the user is a member, False if not (error already sent to the client).
        """
        ok = await self.conversation_service.is_member(
            db=self.db,
            conversation_id=conversation_id,
            user_id=self.user.id
        )
        if not ok :
            await self.ws.send_json(outbound("error" , detail="member not found"))
        return ok

    async def on_message_read(
        self,
        data : dict[str , Any]
    ) -> None :
        """
        Handles a 'message:read' event — marks all unread messages in a conversation as read
        and broadcasts a 'read:update' event to all other members.

        Parameters:
          data (dict[str, Any]): WebSocket payload. Expected key:
            - conversation_id (str): UUID of the conversation to mark as read.

        Returns:
          None
        """
        conversation_id = await self._parse_conversation_id(data)
        if conversation_id is None or not await self._require_member(conversation_id=conversation_id):
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
        """
        Converts a MessageOut Pydantic object into a plain JSON-serializable dict.

        Parameters:
          message: A MessageOut schema object with id, conversation_id, sender_id,
                   content, message_type, created_at, and is_deleted fields.

        Returns:
          dict: A plain dictionary with all fields serialized to JSON-safe types
                (UUIDs as strings, datetime as ISO 8601 string).
        """
        return {
            "id": str(message.id),
            "conversation_id": str(message.conversation_id),
            "sender_id": str(message.sender_id),
            "content": message.content,
            "message_type": message.message_type,
            "created_at": message.created_at.isoformat(),
            "is_deleted": message.is_deleted,
        }
