import uuid
from typing import Annotated, TypeAlias

from fastapi import Cookie, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.converseation.reposetory import ConversetionRepo
from src.dependences import resolve_user_from_token
from src.model import Conversation
from src.user.service import UserService

AccessToken : TypeAlias = Annotated[str | None , Cookie()]

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
    ) -> Conversation | None:

        user1 = await self.user_service.fun_search_user_by_id(
            db,
            user_id
        )

        if user1 is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="USER DOES NOT FOUND"
            )




        user_ids = [user1.id , sender_id]

        res = await self.repo.create_conversation_with_member(
            db,
            user_ids
        )

        return res

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
    # @return:liat[Conversation]
    async def get_coversation_list(
        self,
        db:AsyncSession,
        access_token:str
    ) -> list[Conversation] | None:

        is_user = await resolve_user_from_token(
            db,
            access_token
        )

        res = await self.repo.get_conversation_list(
            db,
            is_user.id
        )
        return res
