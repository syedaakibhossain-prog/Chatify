from sqlalchemy.ext.asyncio import AsyncSession
from src.model import Conversession , Member
from sqlalchemy import select , and_
import uuid


class ConversessionReposetory:
    def __init__(self):
        pass

    async def create_conversession(
        self , 
        db: AsyncSession , 
        conversession:Conversession
    ) -> Conversession:
        
        db.add(conversession)
        await db.flush()

        return conversession

    async def get_converssion_by_id(
        self , 
        db:AsyncSession , 
        conversession_id:uuid.UUID
    ) -> Conversession | None:

        result = await db.execute(
            select(Conversession).where(
             Conversession.id == conversession_id
            )
        )
        
        return result.scalar_one_or_none()

    async def add_member(
        self ,
        db:AsyncSession ,
        member:Member
    ) -> Member:

        db.add(member)
        await db.flush()
        return member

    async def get_member(
        self , 
        db:AsyncSession , 
        user_id:uuid.UUID , 
        conversession_id:uuid.UUID
    ) -> Member | None:

        result = await db.execute(
            select(Member).where(
                and_(
                    Member.user_id == user_id,
                    Member.conversession_id == conversession_id
                )
            )
        )

        return result.scalar_one_or_none()
        
        
        


