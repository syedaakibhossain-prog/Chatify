import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.model import Conversation, Member


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
    ) ->list[Conversation] | None:

        query = await db.execute(
            select(Conversation)
            .join(Member, Member.conversation_id == Conversation.id)
            .where(Member.user_id == user_id)
            .options(selectinload(Conversation.members).selectinload(Member.user))
            .order_by(Conversation.updated_at.desc())
        )
        res = query.scalars().unique().all()
        return list(res)
