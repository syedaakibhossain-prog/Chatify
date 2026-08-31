import uuid
import datetime

from sqlalchemy import String, ForeignKey, DateTime, func, Boolean, false, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    username: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    last_seen: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    conversation_memberships: Mapped[list["Member"]] = relationship(
        "Member",
        back_populates="user",
    )

    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="sender",
    )


class Conversession(BaseModel):
    __tablename__ = "conversessions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    members: Mapped[list["Member"]] = relationship(
        "Member",
        back_populates="conversession",
        cascade="all, delete-orphan",
    )

    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversession",
        cascade="all, delete-orphan",
    )


class Member(BaseModel):
    __tablename__ = "members"

    conversession_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversessions.id"),
        primary_key=True,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        primary_key=True,
        index=True,
    )

    joined_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    conversession: Mapped["Conversession"] = relationship(
        "Conversession",
        back_populates="members",
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="conversation_memberships",
    )


class Message(BaseModel):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    conversession_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversessions.id"),
        nullable=False,
        index=True,
    )

    sender_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    content: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    conversession: Mapped["Conversession"] = relationship(
        "Conversession",
        back_populates="messages",
    )

    sender: Mapped["User"] = relationship(
        "User",
        back_populates="messages",
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
    )

    deleted_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        nullable=True,
    )