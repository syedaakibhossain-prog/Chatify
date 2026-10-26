import uuid

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload
from src.model import Conversation, Member, Message, User


class ConversetionRepo:
    """
    Data access layer for Conversation-related database operations.

    Provides async query methods for creating conversations, checking membership,
    fetching conversation lists, and marking messages as read.
    """

    async def create_conversation_with_member(
        self,
        db:AsyncSession,
        pair_key:str,
        user_ids:list[uuid.UUID]
    ) -> Conversation:
        """
        Creates a new Conversation and adds all given users as Members in one transaction.

        Deduplicates user_ids before inserting to prevent duplicate Member rows.
        Uses db.flush() to get the Conversation.id before inserting Members, then commits.

        Parameters:
          db (AsyncSession)        : The async database session.
          pair_key (str)           : The unique key identifying this pair of users.
          user_ids (list[uuid.UUID]): The UUIDs of all users to add as members.

        Returns:
          Conversation: The newly created and DB-refreshed Conversation ORM object.
        """
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
        """
        Checks whether a specific user is a member of a given conversation.

        Parameters:
          db (AsyncSession)              : The async database session.
          conversation_id (uuid.UUID)    : The UUID of the conversation to check.
          user_id (uuid.UUID)            : The UUID of the user to check.

        Returns:
          bool: True if the user is a member, False otherwise.
        """

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
        """
        Fetches a single Conversation by its UUID primary key.

        Parameters:
          db (AsyncSession)           : The async database session.
          conversation_id (uuid.UUID) : The UUID of the conversation to fetch.

        Returns:
          Conversation | None: The matching Conversation ORM object, or None if not found.
        """

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
        """
        Returns all Conversation objects that a user belongs to, ordered by most recent activity.

        Parameters:
          db (AsyncSession)  : The async database session.
          user_id (uuid.UUID): The UUID of the user whose conversations to fetch.

        Returns:
          list[Conversation]: A list of Conversation ORM objects (may be empty).
        """

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
        """
        Marks all unread messages in a conversation as read, excluding messages sent by the user.

        Executes a bulk UPDATE on the messages table, setting is_read=True for all messages
        in the given conversation that were sent by someone other than user_id and haven't
        been read yet.

        Parameters:
          db (AsyncSession)           : The async database session.
          conversation_id (uuid.UUID) : The UUID of the conversation to mark as read.
          user_id (uuid.UUID)         : The UUID of the user who is reading (their own messages
                                        are excluded from the update).

        Returns:
          None
        """

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
        """
        Looks up an existing Conversation by its pair_key (internal use only).

        Also eagerly loads the conversation's members via selectinload to avoid
        N+1 queries when checking participants.

        Parameters:
          db (AsyncSession) : The async database session.
          pair_key (str)    : The deterministic key for the user-pair (e.g. 'uuid1:uuid2').

        Returns:
          Conversation | None: The matching Conversation with members loaded, or None.
        """

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
        """
        Returns a list of (conversation_id, partner_username) tuples for the given user.

        Uses two aliased Member joins to find the *other* participant in each conversation
        (i.e. the person who is NOT the current user), then joins to User to get their username.
        Results are ordered by conversation.updated_at descending (most recent first).

        Parameters:
          db (AsyncSession)  : The async database session.
          user_id (uuid.UUID): The UUID of the current user.

        Returns:
          list[tuple[uuid.UUID, str]]: List of (conversation_id, other_user_username) rows.
        """

        me = aliased(Member)
        others = aliased(Member)

        query = (
            select(Conversation.id, User.username)
            .join(me, me.conversation_id == Conversation.id)
            .join(others, others.conversation_id == Conversation.id)
            .join(User, User.id == others.user_id)
            .where(me.user_id == user_id)
            .where(others.user_id != user_id)
            .order_by(Conversation.updated_at.desc())
        )

        result = await db.execute(query)
        return result.all()

    async def _get_conversation_ids(
        self,
        db:AsyncSession,
        user_id:uuid.UUID
    ) -> list[uuid.UUID]:
        """
        Returns a flat list of conversation UUIDs that a user is a member of.

        Used internally (e.g. by the WebSocket router) to join a user to all their
        conversation rooms on connection.

        Parameters:
          db (AsyncSession)  : The async database session.
          user_id (uuid.UUID): The UUID of the user.

        Returns:
          list[uuid.UUID]: A list of conversation UUIDs the user belongs to.
        """

        query = await db.execute(
                select(Conversation.id)
                .join(Member, Member.conversation_id == Conversation.id)
                .where(Member.user_id == user_id)
            )
        return list(query.scalars().all())
