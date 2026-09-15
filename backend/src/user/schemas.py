import datetime
import uuid

from pydantic import BaseModel


class UserSearchResults(BaseModel):
    id:uuid.UUID
    username:str
    last_seen:datetime.datetime
