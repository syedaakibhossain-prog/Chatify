import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.model import Conversession, Member
from src.chat.ConversessionReposetory import ConversessionReposetory



class ConversessionService:
    def __init__(
        self,
        reposetory:ConversessionReposetory
    ):

        self.repo = reposetory

    async def create_conversession(
        self,
        db:AsyncSession,
        user_ids:list[uuid.UUID]
    ) -> Conversession:

        conversession = Conversession()

        

        await self.repo.create_conversession(db , conversession)

        for user_id in user_ids:

            member = Member(
                conversession_id = conversession.id,
                user_id = user_id
            )

            await self.repo.add_member(db , member)
            
        return conversession
    
    async def get_conversession(
        self,
        db:AsyncSession,
        conversession_id:uuid.UUID,
    ) -> Conversession | None:
        
        return await self.repo.get_converssion_by_id(db , conversession_id)

    async def is_member(
        self,
        db:AsyncSession,
        user_id:uuid.UUID,
        conversession_id:uuid.UUID
    ) -> bool:

        return (await self.repo.get_member(db , user_id , conversession_id)) is not None
    