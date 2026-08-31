from fastapi import FastAPI
from sqlalchemy import and_
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.model import Message


class MessageReposetory:
    def __init__(self):
        pass

    async def create_message(
        self,
        db:AsyncSession,
        message:Message
    ) -> Message:

        db.add(message)
        await db.flush()
        await db.refresh(message)

        return message

    async def get_message_by_id(
        self,
        db:AsyncSession,
        message_id:uuid.UUID
    ) -> Message | None:

        result = await db.execute(
            select(Message).where(
                Message.id == message_id
            )
        )

        return result.scalar_one_or_none()


    async def get_all_messages(
        self,
        db:AsyncSession,
        conversession_id:uuid.UUID,
        limit: int = 50
    ) -> list[Message] | None:

        print("CONVERSESSION ID" , conversession_id)
        
        results = await db.execute(
            select(Message).where(
                and_(
                    Message.conversession_id == conversession_id,
                    Message.is_deleted.is_(False)
                )
            ).order_by(Message.created_at.desc())
            .limit(limit)
        )

        messages = list(results.scalars().all())



        print("MESSAGES WITHOUT is_deleted FILTER:", messages)

        for message in messages:
            print(
                "ID:", message.id,
                "CONVERSATION:", message.conversession_id,
                "DELETED:", message.is_deleted,
                "CONTENT:", message.content,
            )
        return messages

    
    async def delete_message(
        self,
        db:AsyncSession,
        message_id:uuid.UUID,
    ) -> bool:

        result = await db.execute(
            select(Message).where(
                Message.id == message_id
            )
        )

        message = result.scalar_one_or_none()
        if not message:
            return False

        message.is_deleted = True
        message.deleted_at = func.now()
        await db.flush()
        return True

