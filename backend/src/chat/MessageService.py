import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.model import Message
from src.chat.MessageReposetory import MessageReposetory
from src.chat.ConversessionService import ConversessionService
from src.chat.schemas import MessageCreate


class MessageService:

    def __init__(
        self,
        message_reposetory: MessageReposetory,
        conversession_service: ConversessionService,
    ):
        self.message_repo = message_reposetory
        self.conversession_service = conversession_service

    async def send_message(
        self,
        db: AsyncSession,
        message_data: MessageCreate,
        conversession_id: uuid.UUID,
        sender_id: uuid.UUID,
    ) -> Message:

        conversation = await (
            self.conversession_service.get_conversession(
                db,
                conversession_id,
            )
        )

        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation doesn't exist",
            )

        is_member = await self.conversession_service.is_member(
            db,
            sender_id,
            conversession_id,
        )

        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this conversation",
            )

        message = Message(
            conversession_id=conversession_id,
            sender_id=sender_id,
            content=message_data.content,
        )


        created_message = await self.message_repo.create_message(
            db,
            message,
        )

        await db.commit()

        return created_message

    async def get_messages(
        self,
        db: AsyncSession,
        conversession_id: uuid.UUID,
        user_id: uuid.UUID,
        limit: int = 50,
    ) -> list[Message]:

        conversation = await (
            self.conversession_service.get_conversession(
                db,
                conversession_id,
            )
        )

        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation doesn't exist",
            )

        is_member = await self.conversession_service.is_member(
            db,
            user_id,
            conversession_id,
        )

        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this conversation",
            )

        return await self.message_repo.get_all_messages(
            db,
            conversession_id,
            limit,
        )

    async def delete_message(
        self,
        db: AsyncSession,
        message_id: uuid.UUID,
        sender_id: uuid.UUID,
    ) -> Message:

        message = await self.message_repo.get_message_by_id(
            db,
            message_id,
        )

        if message is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message doesn't exist",
            )

        if message.sender_id != sender_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to delete this message",
            )

        if message.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message is already deleted",
            )

        async with db.begin():
            deleted_message = await self.message_repo.delete_message(
                db,
                message_id,
            )

        return deleted_message

    async def update_message(
        self,
        db: AsyncSession,
        message_id: uuid.UUID,
        sender_id: uuid.UUID,
        content: str,
    ) -> Message:

        message = await self.message_repo.get_message_by_id(
            db,
            message_id,
        )

        if message is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message doesn't exist",
            )

        if message.sender_id != sender_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to update this message",
            )

        if message.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deleted messages cannot be edited",
            )

        async with db.begin():
            updated_message = await self.message_repo.update_message(
                db,
                message_id,
                content,
            )

        return updated_message