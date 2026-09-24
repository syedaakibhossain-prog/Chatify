import uuid
from typing import Annotated, TypeAlias

from fastapi import Cookie, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.converseation.reposetory import ConversetionRepo
from src.dependences import resolve_user_from_token
from src.model import Conversation
from src.user.service import UserService

from src.converseation.schemas import ConversationResponse

AccessToken : TypeAlias = Annotated[str | None , Cookie()]

def _pair_key(
    a: uuid.UUID,
    b: uuid.UUID
) -> str:

    x,y = sorted([str(a) , str(b)])

    return f"{x}:{y}"

class ConversationService:
    def __init__(
        self,
        conversation_repo:ConversetionRepo,
        user_service:UserService
    ) -> None:
        self.repo = conversation_repo
        self.user_service = user_service

    # @dec: create conversation using member
    # it was also verify user from access token , and user_id
    # @parameter:db
    # @parameter:user_id
    # @parameter:access_token
    # @return:Conversation
    async def create_conversation_with_member(
        self,
        db:AsyncSession,
        user_id:uuid.UUID,
        sender_id : uuid.UUID
    ) -> ConversationResponse | None:
        print(f"[DEBUG] create_conversation: user_id={user_id!r}  sender_id={sender_id!r}  match={user_id == sender_id}")
        if user_id == sender_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create a conversation with yourself",
            )

        user1 = await self.user_service.fun_search_user_by_id(
            db,
            user_id
        )

        if user1 is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="USER DOES NOT FOUND"
            )


        pair_key = _pair_key(
            user1.id,
            sender_id
        )
        existing_conversation = await self.repo._get_conv_by_pair_key(
            db,
            pair_key
        )

        if existing_conversation :
            return ConversationResponse(
                id=existing_conversation.id,
                other_username=user1.username
            )

        user_ids = [user1.id , sender_id]

        conversation = await self.repo.create_conversation_with_member(
            db,
            pair_key,
            user_ids
        )



        return ConversationResponse(
            id=conversation.id,
            other_username=user1.username
        )

    # @dec: get conversation useing conversation id
    # @parameter:db
    # @parameter:access_token
    # @parameter:conversation_id
    # @return: Conversation
    async def get_conversation(
        self,
        db:AsyncSession,
        access_token:str,
        conversation_id:uuid.UUID
    ) -> Conversation | None:

        is_user = await resolve_user_from_token(
            db,
            access_token
        )

        if not await self.repo.is_member(
            db,
            conversation_id,
            is_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="YOU ARE NOT A MEMBER OF THIS CONVERSATION"
            )

        res = await self.repo.get_conversation_by_id(
            db,
            conversation_id
        )
        return res

    # @dec: get the conversation list for user from acces_token
    # @parameter:db
    # @parameter:access_token
    # @return:liat[Conversation.id]
    async def get_coversation_list(
        self,
        db:AsyncSession,
        access_token:str
    ) -> list[ConversationResponse]:

        is_user = await resolve_user_from_token(
            db,
            access_token
        )

        rows = await self.repo.get_conversation_list_with_partners(db, is_user.id)
        return [
            ConversationResponse(id=conv_id, other_username=username)
            for conv_id, username in rows
        ]
    async def is_member(
        self,
        db:AsyncSession,
        conversation_id:uuid.UUID,
        user_id:uuid.UUID
    ) -> bool :

        return await self.repo.is_member(
            db,
            conversation_id,
            user_id
        )



    async def mark_conversation_read(
        self,
        db : AsyncSession,
        conversation_id : uuid.UUID,
        user_id : uuid.UUID
    ) -> None :
        await self.repo.mark_conversation_read(
            db,
            conversation_id,
            user_id
        )
    async def get_conversation_ids_for_user(
        self,
        db:AsyncSession,
        user_id:uuid.UUID
    ) ->list[uuid.UUID]:

        return await self.repo._get_conversation_ids(
            db,
            user_id
        )
