import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class CreateMessage(BaseModel) :
    content:str = Field(..., min_length= 1 , max_length=1000 )

class MessageOut(BaseModel) :
    model_config = ConfigDict(from_attributes=True)
    id : uuid.UUID
    conversation_id : uuid.UUID
    sender_id : uuid.UUID
    content : str
    message_type : str
    created_at: datetime.datetime
    is_deleted : bool

class Messages(BaseModel) :
    messages : list[MessageOut]
