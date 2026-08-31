import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.chat.schemas import (
    ConversationCreate,
    ConversationResponse,
)
from src.chat.ConversessionService import ConversessionService
from src.chat.ConversessionReposetory import ConversessionReposetory
from src.dependences import get_user


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


def get_conversation_service() -> ConversessionService:
    repository = ConversessionReposetory()

    return ConversessionService(repository)


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    data: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_user),
    service: ConversessionService = Depends(
        get_conversation_service
    ),
):
    # Add authenticated user to the conversation
    user_ids = list(
        set(
            data.user_ids + [current_user.id]
        )
    )

    # A conversation requires at least two users
    if len(user_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A conversation requires at least two members",
        )

    conversation = await service.create_conversession(
        db,
        user_ids,
    )

    await db.commit()

    return conversation


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_user),
    service: ConversessionService = Depends(
        get_conversation_service
    ),
):
    # Check whether conversation exists
    conversation = await service.get_conversession(
        db,
        conversation_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # Check whether current user belongs to conversation
    is_member = await service.is_member(
        db,
        current_user.id,
        conversation_id,
    )

    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this conversation",
        )

    return conversation