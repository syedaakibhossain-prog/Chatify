from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from src.config import settings


class BaseModel(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models in the application.

    All database table models (User, Conversation, Member, Message) inherit
    from this class. SQLAlchemy uses it to track metadata and generate
    the schema via `BaseModel.metadata.create_all()`.
    """
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
    """
    FastAPI dependency that provides a database session per request.

    Opens an async SQLAlchemy session, yields it for use inside a route or
    dependency, then automatically closes it when the request is done.

    Parameters:
      None

    Yields:
      AsyncSession: An active async database session ready for queries.
    """
    async with SessionLocal() as db:
        yield db
