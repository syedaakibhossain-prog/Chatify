import uuid
from typing import Annotated, TypeAlias

from fastapi import APIRouter, Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.converseation.reposetory import ConversetionRepo
from src.converseation.service import ConversationService
from src.database import get_db
from src.dependences import resolve_user_from_token
from src.model import Conversation
from src.user.reposetory import UserRepo
from src.user.service import UserService

from src.converseation.schemas import ConversationResponse

router = APIRouter(
    prefix="/api/v1/conversation",
    tags=["conversation"]
)

Dbsession = Annotated[AsyncSession , Depends(get_db)]

AccessToken : TypeAlias = Annotated[str | None , Cookie()]

def get_user_service() -> UserService:
    user_repo = UserRepo()

    return UserService(
        user_repo
    )

user_service = Annotated[UserService , Depends(get_user_service)]

def get_conversation_service(service:user_service) -> ConversationService:
    coversation_repo = ConversetionRepo()

    return ConversationService(
        coversation_repo,
        service
    )

conversation = Annotated[ConversationService , Depends(get_conversation_service)]

@router.post("/" , response_model=None)
async def create_conversation(
    db:Dbsession,
    user_id:uuid.UUID,
    service:conversation,
    access_token:AccessToken = None,
) -> ConversationResponse | None:

    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ACCESS TOKEN NoT PROVIDED"
        )

    sender = await resolve_user_from_token(
        db,
        access_token
    )
    if sender is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="NOT AUTHORIZE"
        )
    response = await service.create_conversation_with_member(
        db,
        user_id,
        sender.id
    )

    return response

@router.get("/" , response_model=None)
async def list_my_conversession(
    db:Dbsession,
    service:conversation,
    access_token:AccessToken = None,
) -> list[ConversationResponse]:
    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ACCESS TOKEN NOT PROVIDED"
        )
    return await service.get_coversation_list(
        db,
        access_token
    )

@router.get("/{conversation_id}" , response_model= None)
async def get_conversation(
    db:Dbsession,
    conversation_id:uuid.UUID,
    service:conversation,
    access_token:AccessToken = None,
) -> Conversation | None:

    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ACCESS TOKEN NOT PROVIDED"
        )

    return await service.get_conversation(
        db,
        access_token,
        conversation_id
    )
