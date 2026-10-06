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
    def __init__(
        self,
        message_repo:MessageRepo,
        conversation_service:ConversationService
    ) -> None:
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
