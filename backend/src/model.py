import datetime
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import BaseModel


class User(BaseModel):
    """
    ORM model representing the 'users' database table.

    Stores each registered user's account information.

    Columns:
      id (UUID)            : Primary key, auto-generated UUID.
      username (str)       : Unique display name, max 20 characters.
      name (str)           : Optional full name, max 20 characters.
      email (str)          : Unique email address, max 120 characters.
      hashed_password (str): Bcrypt-hashed password string, max 255 characters.
      last_seen (datetime) : Timestamp of the user's last activity (UTC).

    Relationships:
      conversation_memberships: All Member rows linking this user to conversations.
      messages               : All messages sent by this user.
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    username: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(20), nullable=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    last_seen: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    conversation_memberships: Mapped[list["Member"]] = relationship(
        "Member", back_populates="user"
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="sender"
    )


class Conversation(BaseModel):
    """
    ORM model representing the 'conversations' database table.

    Each row represents a unique 1-on-1 chat channel between two users.

    Columns:
      id (UUID)         : Primary key, auto-generated UUID.
      created_at        : UTC timestamp when the conversation was first created.
      is_read (bool)    : Whether the conversation has been read (currently unused for groups).
      updated_at        : UTC timestamp that auto-updates on every change; indexed for fast
                          sorting of the chat list by most-recent activity.
      pair_key (str)    : Deterministic key derived from both user UUIDs (sorted and joined
                          with ':') to guarantee uniqueness and prevent duplicate conversations.

    Relationships:
      members  : List of Member rows (the two participants).
      messages : All messages belonging to this conversation.
    """
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    # is_group: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # title: Mapped[str | None] = mapped_column(String(80), nullable=True)  # for groups

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_read : Mapped[bool] = mapped_column(
        Boolean , nullable=True , default=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,   # for chat-list sorting
    )
    pair_key:Mapped[str] = mapped_column(
        String ,
        nullable=False,
        index=True
    )
    members: Mapped[list["Member"]] = relationship(
        "Member", back_populates="conversation", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )


class Member(BaseModel):
    """
    ORM model representing the 'members' database table.

    A join table linking users to conversations (many-to-many).
    Each row records one user's membership in one conversation.

    Columns:
      conversation_id (UUID): FK to conversations.id; part of composite PK.
      user_id (UUID)        : FK to users.id; part of composite PK.
      joined_at (datetime)  : UTC timestamp when the user joined the conversation.
      last_read_at (datetime): UTC timestamp of the last message the user read
                               (nullable — None if the user has never opened the chat).

    Relationships:
      conversation : The parent Conversation object.
      user         : The parent User object.
    """
    __tablename__ = "members"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("conversations.id"), primary_key=True, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), primary_key=True, index=True
    )
    joined_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_read_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="members"
    )
    user: Mapped["User"] = relationship("User", back_populates="conversation_memberships")


class Message(BaseModel):
    """
    ORM model representing the 'messages' database table.

    Each row stores a single chat message sent inside a conversation.

    Columns:
      id (UUID)              : Primary key, auto-generated UUID.
      conversation_id (UUID) : FK to the conversation this message belongs to.
      sender_id (UUID)       : FK to the user who sent the message.
      content (str)          : The message body text, max 1000 characters.
      message_type (str)     : Type of message (e.g. 'text'), max 20 characters.
      created_at (datetime)  : UTC timestamp when the message was created; indexed
                               for efficient time-based queries.
      is_read (bool)         : Whether the recipient has read this message.
      is_deleted (bool)      : Soft-delete flag; True if the message was deleted.
      deleted_at (datetime)  : UTC timestamp of when the message was soft-deleted
                               (nullable — None if the message is not deleted).

    Relationships:
      conversation : The parent Conversation object.
      sender       : The User who sent the message.
    """
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(String(1000), nullable=False)
    message_type: Mapped[str] = mapped_column(String(20), default="text", nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    is_read : Mapped[bool] = mapped_column(
        Boolean , nullable=True , default=False
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", nullable=False
    )
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )
    sender: Mapped["User"] = relationship("User", back_populates="messages")
