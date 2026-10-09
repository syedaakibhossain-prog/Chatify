import datetime
import uuid
from typing import Optional

from sqlalchemy import or_, and_, select
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
        db: AsyncSession,
        conversation_id: uuid.UUID,
        limit: int = 10,
        before: Optional[datetime.datetime] = None,
        before_id: Optional[uuid.UUID] = None,
    ) -> Messages:

        query = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id
            )
        )

        if before is not None and before_id is not None:
            query = query.where(
                or_(
                    Message.created_at < before,
                    and_(
                        Message.created_at == before,
                        Message.id < before_id,
                    ),
                )
            )

        query = query.order_by(Message.created_at.desc(), Message.id.desc()).limit(limit)
        result = await db.execute(query)
        rows = list(result.scalars().all())[::-1]
        return Messages(
            messages=rows
        )
