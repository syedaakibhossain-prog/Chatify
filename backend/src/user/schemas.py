import datetime
import uuid

from pydantic import BaseModel


class UserSearchResults(BaseModel):
    id:uuid.UUID
    username:str
    last_seen:datetime.datetime

class UserResults(BaseModel):
    id:uuid.UUID
    username:str
