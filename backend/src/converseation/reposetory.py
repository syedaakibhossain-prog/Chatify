import uuid

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload
from src.model import Conversation, Member, Message, User


class ConversetionRepo:

    async def create_conversation_with_member(
        self,
        db:AsyncSession,
        pair_key:str,
        user_ids:list[uuid.UUID]
    ) -> Conversation:
        unique_user_ids = list(dict.fromkeys(user_ids))
        conv = Conversation(pair_key=pair_key)
        db.add(conv)
        await db.flush()

        db.add_all(
                Member(conversation_id=conv.id, user_id=uid)
                for uid in unique_user_ids
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
    ) ->list[Conversation] | None:

        query = await db.execute(
            select(Conversation)
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

    async def _get_conv_by_pair_key(
        self,
        db:AsyncSession,
        pair_key:str
    ) -> Conversation | None:

        query = await db.execute(
            select(Conversation)
            .where(
                Conversation.pair_key == pair_key
            )
            .options(selectinload(Conversation.members))
        )
        res = query.scalar_one_or_none()
        return res

    async def get_conversation_list_with_partners(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[tuple[uuid.UUID, str]]:

        me = aliased(Member)
        others = aliased(Member)

        stmt = (
            select(Conversation.id, User.username)
            .join(me, me.conversation_id == Conversation.id)
            .join(others, others.conversation_id == Conversation.id)
            .join(User, User.id == others.user_id)
            .where(me.user_id == user_id)
            .where(others.user_id != user_id)
            .order_by(Conversation.updated_at.desc())
        )

        result = await db.execute(stmt)
        return result.all()

    async def _get_conversation_ids(
        self,
        db:AsyncSession,
        user_id:uuid.UUID
    ) -> list[uuid.UUID]:

        query = await db.execute(
                select(Conversation.id)
                .join(Member, Member.conversation_id == Conversation.id)
                .where(Member.user_id == user_id)
            )
        return list(query.scalars().all())
