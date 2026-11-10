import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.message.schemas import MessageOut, Messages
from src.model import Message


class MessageRepo:
    """
    Data access layer for Message records.

    Provides async methods to persist new messages and retrieve
    all messages belonging to a specific conversation.
    """


    async def send_message(
        self,
        db : AsyncSession,
        message: Message
    ) -> MessageOut :
        """
        Persists a new Message to the database and returns its serialized form.

        Parameters:
          db (AsyncSession) : The async database session.
          message (Message) : The Message ORM instance to insert (conversation_id, sender_id,
                              and content must already be set).

        Returns:
          MessageOut: A Pydantic schema populated with the DB-generated fields (id, created_at, etc.).
        """

        db.add(message)
        await db.commit()
        await db.refresh(message)

        return MessageOut(
            id=message.id,
            conversation_id=message.conversation_id,
            sender_id=message.sender_id,
            content=message.content,
            message_type=message.message_type,
            created_at=message.created_at,
            is_deleted=message.is_deleted
        )

    async def fecth_messages(
        self,
        db : AsyncSession,
        conversation_id : uuid.UUID
    ) -> Messages :
        """
        Retrieves all messages in a given conversation.

        Parameters:
          db (AsyncSession)           : The async database session.
          conversation_id (uuid.UUID) : The UUID of the conversation whose messages to fetch.

        Returns:
          Messages: A Pydantic wrapper containing a list of MessageOut schemas.
        """

        query = await db.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation_id
            )
        )

        res = query.scalars().all()
        return Messages(
            messages=[MessageOut.model_validate(m) for m in res]
        )
