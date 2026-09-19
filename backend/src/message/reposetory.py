import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.message.schemas import MessageOut, Messages
from src.model import Message


class MessageRepo:


    async def send_message(
        self,
        db : AsyncSession,
        message: Message
    ) -> MessageOut :

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
