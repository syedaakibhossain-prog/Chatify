import uuid

from pydantic import BaseModel


class ConversationId(BaseModel):
    id : uuid.UUID

class Conversations(BaseModel):
    converseton_ids : list[ConversationId]
