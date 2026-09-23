import uuid
from typing import Annotated, TypeAlias

from fastapi import APIRouter, Cookie, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.message.reposetory import MessageRepo
from src.message.schemas import Messages
from src.message.service import MessageService

router = APIRouter(
    prefix="/api/v1/message",
    tags=["message"]
)


DbSession = Annotated[AsyncSession , Depends(get_db)]
AccessToken : TypeAlias = Annotated[str | None , Cookie()]


def get_message_service() -> MessageService :
    message_repo = MessageRepo()

    return MessageService(
        message_repo
    )

message_service = Annotated[MessageService , Depends(get_message_service)]

# message send (auth required)
# @router.post(
#     "/conversations/{conversation_id}/messages",
#     response_model=MessageOut
# )
# async def send_message(
#     conversation_id : uuid.UUID,
#     db : DbSession,
#     payload : CreateMessage,
#     access_token : AccessToken,
#     service : message_service
# ) -> MessageOut :

#     if payload.content is None :
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="content is empty"
#         )

#     res = await service.send_message(
#         db,
#         conversation_id,
#         payload,
#         access_token
#     )

#     return res

#get all message from a perticular convversation
@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=Messages
)
async def get_all_message(
    db : DbSession,
    conversation_id : uuid.UUID,
    access_token : AccessToken,
    service : message_service
) ->Messages :

    return await service.get_messages(
        db,
        conversation_id,
        access_token
    )
