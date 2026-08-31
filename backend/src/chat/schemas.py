from datetime import datetime
import uuid

from pydantic import BaseModel, Field, ConfigDict


class ConversationCreate(BaseModel):
    user_ids: list[uuid.UUID] = Field(min_length=1)


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID


class MessageCreate(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=1000,
    )


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversession_id: uuid.UUID
    sender_id: uuid.UUID
    content: str
    created_at: datetime
    is_deleted: bool
    deleted_at: datetime | None