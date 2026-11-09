import json
import logging
from typing import Any

from cachetools import TTLCache
from fastapi import Depends

from src.redis.redisClient import get_redis

logger = logging.getLogger(__name__)

_local_cache = TTLCache(maxsize=10_000 , ttl=60)

class CacheService:

    def __init__(
        self,
        redis_client:Depends(get_redis)
    ) -> None:

        self._redis = redis_client

    async def _set(
        self,
        key:str,
        value:Any,
        ttl:int = 300
    ):
        _local_cache[key] = value

        await self._redis.set(key , json.dumps(value) , ex=ttl)

    async def _get(
        self,
        key:str
    ) -> Any | None:

        if key in _local_cache:
            return _local_cache[key]

        raw = await self._redis.get(key)
        if raw:
            data = json.dumps(raw)

            _local_cache[key] = data

            return data

        return None

    async def _delete(
        self,
        key:str
    ) -> None:

        if key in _local_cache:
            del _local_cache[key]
        await self._redis.delete(key)

#     async def _cache(
#         self,
#         key:str,
#         loader:Callable[[], Awaitable[Any]],
#         ttl:int
#     ) -> Any | None:
#
#         chached = await self._get(key=key)
#
#         if chached is not None:
#             return chached
#
#         value = loader()
#
#         if value is not None:
#             await self._set(
#                 key=key,
#                 value=value,
#                 ttl=ttl
#             )
#         return value
