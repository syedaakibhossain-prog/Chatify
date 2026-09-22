from typing import Any, Literal, TypedDict


class InboundMessage(TypedDict, total=False):
    type: Literal[
        "message:send",
        "message:read",
        "typing:start",
        "typing:stop",
        "ping",
    ]
    conversation_id: str
    content: str
    temp_id: str
    message_id: str


def outbound(event_type: str, **kwargs: Any) -> dict[str, Any]:
    return {"type": event_type, **kwargs}
