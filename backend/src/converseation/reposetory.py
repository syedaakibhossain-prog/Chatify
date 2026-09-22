import uuid

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.model import Conversation, Member, Message


class ConversetionRepo:

    async def create_conversation_with_member(
        self,
        db:AsyncSession,
        user_ids:list[uuid.UUID]
    ) -> Conversation:
        conv = Conversation()
        db.add(conv)
        await db.flush()

        db.add_all(
            Member(conversation_id = conv.id , user_id = uid)
            for uid in user_ids
        )
        await db.commit()
        await db.refresh(conv)
        return conv

    async def is_member(
        self,
        db:AsyncSession,
        conversation_id:uuid.UUID,
        user_id:uuid.UUID
    ) -> bool:

        query = await db.execute(
            select(Member)
            .where(
                and_(
                    Member.conversation_id == conversation_id,
                    Member.user_id == user_id
                )

            )
        )

        responce = query.scalar()

        return bool(responce)

    async def get_conversation_by_id(
        self,
        db:AsyncSession,
        conversation_id:uuid.UUID
    ) -> Conversation | None:

        query = await db.execute(
            select(Conversation)
            .where(
                Conversation.id == conversation_id
            )
        )
        res = query.scalar_one_or_none()

        return res

    async def get_conversation_list(
        self,
        db:AsyncSession,
        user_id:uuid.UUID
    ) ->list[uuid.UUID] | None:

        query = await db.execute(
            select(Conversation.id)
            .join(Member, Member.conversation_id == Conversation.id)
            .where(Member.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
        res = query.scalars().all()
        return list(res)

    async def mark_conversation_read(
        self,
        db : AsyncSession,
        conversation_id : uuid.UUID,
        user_id : uuid.UUID
    ) -> None :

        await db.execute(
            update(Message)
            .where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.sender_id != user_id,
                    Message.is_read == False
                )
            )
            .values(is_read = True)
        )
        await db.commit()
