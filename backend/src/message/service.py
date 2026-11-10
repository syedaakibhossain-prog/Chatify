import uuid
from typing import Annotated, TypeAlias

from fastapi import Cookie, HTTPException, status
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.converseation.service import ConversationService
from src.dependences import resolve_user_from_token
from src.message.reposetory import MessageRepo
from src.message.schemas import CreateMessage, MessageOut, Messages
from src.model import Message

AccessToken : TypeAlias = Annotated [str | None , Cookie()]

class MessageService:
    """
    Service layer for all message-related business logic.

    Depends on MessageRepo for DB access and ConversationService to verify
    that users are members of a conversation before allowing message operations.
    """
    def __init__(
        self,
        message_repo:MessageRepo,
        conversation_service:ConversationService
    ) -> None:
        """
        Initializes the MessageService.

        Parameters:
          message_repo (MessageRepo)             : Repository for reading/writing messages.
          conversation_service (ConversationService): Used to verify conversation membership.
        """
        self.message_repo = message_repo
        self.con_servoice = conversation_service

    #send message (auth required)
    #  @parameter : db
    # @parameter : conversation_id
    # @parameter : payload : content
    # @parameter : acess_token
    # @return  : MessageOut
    async def send_message(
        self,
        db : AsyncSession,
        conversation_id : uuid.UUID,
        payload : CreateMessage,
        access_token : AccessToken
    ) -> MessageOut:
        """
        Sends a message to a conversation after verifying the user from their access token.

        Steps:
          1. Resolves the user from the access token (raises 401 if invalid).
          2. Creates a Message ORM object with the conversation, sender, and content.
          3. Persists the message via the repository.

        Parameters:
          db (AsyncSession)           : The async database session.
          conversation_id (uuid.UUID) : The UUID of the conversation to send the message to.
          payload (CreateMessage)     : Pydantic schema containing the message content string.
          access_token (AccessToken)  : The JWT access token cookie value for authentication.

        Returns:
          MessageOut: The newly created message in serialized Pydantic form.

        Raises:
          HTTPException (401): If the access token is missing or invalid.
        """
        #varify the user
        user = await resolve_user_from_token(
            db,
            access_token
        )
        if user is None :
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="YOU ARE NOT AN USER"
            )

        message = Message(
            conversation_id=conversation_id,
            sender_id=user.id,
            content=payload.content
        )

        res = await self.message_repo.send_message(
            db,
            message
        )
        return res

    #get all the message from perticular conversation
    # @parameter : db
    # @parameter : conversation_id
    # @parameter : access_token
    # @return : Messages : list [MessageOut]
    async def get_messages(
        self,
        db : AsyncSession,
        conversation_id : uuid.UUID,
        user_id:uuid.UUID
    ) -> Messages :
        """
        Retrieves all messages from a conversation, ensuring the user is a member.

        Parameters:
          db (AsyncSession)           : The async database session.
          conversation_id (uuid.UUID) : The UUID of the conversation to fetch messages from.
          user_id (uuid.UUID)         : The UUID of the requesting user (used for membership check).

        Returns:
          Messages: A Pydantic wrapper containing a list of MessageOut schemas.

        Raises:
          HTTPException (404): If the user is not a member of the conversation.
        """

        if not await self.con_servoice.is_member(
            db,
            conversation_id,
            user_id
        ):
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "conversation not found"
            )

        res = await self.message_repo.fecth_messages(
            db,
            conversation_id
        )

        return res

    # Create a message directly (for WebSocket handler where user is already authenticated)
    async def create_message(
        self,
        db : AsyncSession,
        conversation_id : uuid.UUID,
        sender_id : uuid.UUID,
        content : str,
    ) -> MessageOut:
        """
        Creates and persists a message directly without re-authenticating via token.

        Intended for use by the WebSocket handler, where the user has already been
        authenticated during the WebSocket handshake.

        Parameters:
          db (AsyncSession)           : The async database session.
          conversation_id (uuid.UUID) : The UUID of the conversation to post the message to.
          sender_id (uuid.UUID)       : The UUID of the authenticated sender.
          content (str)               : The raw text content of the message.

        Returns:
          MessageOut: The newly created message in serialized Pydantic form.
        """
        payload = CreateMessage(content=content)
        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=payload.content
        )

        res = await self.message_repo.send_message(
            db,
            message
        )
        return res
