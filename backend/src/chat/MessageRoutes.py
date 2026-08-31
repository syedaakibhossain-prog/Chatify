import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependences import get_user

from src.chat.schemas import (
    MessageCreate,
    MessageResponse,
)

from src.chat.MessageService import MessageService
from src.chat.MessageReposetory import MessageReposetory
from src.chat.ConversessionReposetory import ConversessionReposetory
from src.chat.ConversessionService import ConversessionService


router = APIRouter(
    prefix="/messages",
    tags=["Messages"],
)


def get_message_service() -> MessageService:

    conversession_repository = ConversessionReposetory()

    conversession_service = ConversessionService(
        conversession_repository
    )

    message_repository = MessageReposetory()

    return MessageService(
        message_repository,
        conversession_service,
    )


# SEND MESSAGE

@router.post(
    "/conversations/{conversession_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversession_id: uuid.UUID,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_user),
    service: MessageService = Depends(
        get_message_service
    ),
):
    message = await service.send_message(
        db=db,
        message_data=data,
        conversession_id=conversession_id,
        sender_id=current_user.id,
    )

    return message


# GET MESSAGES

@router.get(
    "/conversations/{conversession_id}",
    response_model=list[MessageResponse],
    status_code=status.HTTP_200_OK,
)
async def get_messages(
    conversession_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_user),
    service: MessageService = Depends(
        get_message_service
    ),
):
    messages = await service.get_messages(
        db=db,
        conversession_id=conversession_id,
        user_id=current_user.id,
    )

    return messages


# UPDATE MESSAGE

@router.patch(
    "/{message_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def update_message(
    message_id: uuid.UUID,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_user),
    service: MessageService = Depends(
        get_message_service
    ),
):
    message = await service.update_message(
        db=db,
        message_id=message_id,
        sender_id=current_user.id,
        content=data.content,
    )

    return message


# DELETE MESSAGE

@router.delete(
    "/{message_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_message(
    message_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_user),
    service: MessageService = Depends(
        get_message_service
    ),
):
    message = await service.delete_message(
        db=db,
        message_id=message_id,
        sender_id=current_user.id,
    )

    return message