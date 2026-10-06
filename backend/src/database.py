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
_connect_args = {} if DATABASE_URL.startswith("sqlite") else {"ssl": "require"}

engine = create_async_engine(
    DATABASE_URL,
    connect_args=_connect_args,
    echo=settings.DEBUG,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with SessionLocal() as db:
        yield db
