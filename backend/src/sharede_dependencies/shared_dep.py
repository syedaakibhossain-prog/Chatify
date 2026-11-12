from typing import Annotated

from fastapi import BackgroundTasks, Depends
from src.cache.cache import CacheService
from src.converseation.reposetory import ConversetionRepo
from src.converseation.service import ConversationService
from src.redis.redisClient import RedisClient, get_redis
from src.user.service import UserService

from src.user.reposetory import UserRepo

user_service = Annotated[UserService , Depends(get_user_service)]
redis = Annotated[RedisClient , Depends(get_redis)]

def get_conversation_service(
    service:user_service,
    redis:redis
) -> ConversationService:
    conversation_repo = ConversetionRepo(
        CacheService(
            redis
        )
    )
    return ConversationService(
        conversation_repo=conversation_repo,
        user_service=service,
        _cache_service=CacheService(
            redis
        )
    )

def get_user_service(
    background_task:BackgroundTasks,
    redis:redis
) -> UserService:
    user_repo = UserRepo(
        cahe_ser=CacheService(
            redis
        ),
        background_task=background_task
    )

    return UserService(
        user_repo,
        cache_ser=CacheService(
            redis
        )
    )
