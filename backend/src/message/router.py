import uuid
from typing import Annotated, TypeAlias

from fastapi import APIRouter, Cookie, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.model import User
from src.database import get_db
from src.message.reposetory import MessageRepo
from src.message.schemas import Messages
from src.message.service import MessageService
from src.redis.ratelimiter import rate_limit
from src.redis.ratelimits import MESSAGE_HISTORY
from src.dependences import get_user
from src.converseation.service import ConversationService
from src.converseation.reposetory import ConversetionRepo
from src.user.service import UserService
from src.user.reposetory import UserRepo


router = APIRouter(
    prefix="/api/v1/message",
    tags=["message"]
)


DbSession = Annotated[AsyncSession , Depends(get_db)]
AccessToken : TypeAlias = Annotated[str | None , Cookie()]

def get_user_service() -> UserService:
    user_repo = UserRepo()
    return UserService(
        user_repo
    )
user_service = Annotated[UserService,Depends(get_user_service)]
def get_con_service(user_service:user_service) -> ConversationService:
    conn_service = ConversetionRepo()

    return ConversationService(
        conn_service,
        user_service
    )

conversation_service = Annotated[ConversationService , Depends(get_con_service)]


def get_message_service(conversation_service:conversation_service) -> MessageService :
    message_repo = MessageRepo()

    return MessageService(
        message_repo,
        conversation_service
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

#get all message from a particular conversation
@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=Messages,
    dependencies=[Depends(rate_limit("message:history", MESSAGE_HISTORY))],
)
async def get_all_message(
    db : DbSession,
    conversation_id : uuid.UUID,
    user:Annotated[User , Depends(get_user)],
    service : message_service
) ->Messages :

    return await service.get_messages(
        db,
        conversation_id,
        user.id
    )
