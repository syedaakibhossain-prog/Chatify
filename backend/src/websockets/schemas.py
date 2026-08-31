from pydantic import BaseModel , Field

class WebSocketMessage(BaseModel):
    type: str
    content: str = Field(
        min_length=1,
        max_length=1000
    )