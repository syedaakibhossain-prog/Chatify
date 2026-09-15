from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from src.config import settings


class BaseModel(DeclarativeBase):
    pass


DATABASE_URL = settings.DATABASE_URL


engine = create_async_engine(
    DATABASE_URL,
    echo=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with SessionLocal() as db:
        yield db