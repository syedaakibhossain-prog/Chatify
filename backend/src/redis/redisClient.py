import redis.asyncio as redis
from src.config import settings


class RedisClient:
    _client:redis.Redis | None = None

    @classmethod
    def get(cls) -> redis.Redis:
        if cls._client is None:
            cls._client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=2,
                socket_keepalive=True,
                health_check_interval=30,
            )
        return cls._client

    @classmethod
    async def close(cls) -> None:
        if cls._client is not None:
            await cls._client.close()
            cls._client = None
def get_redis() -> redis.Redis:
    return RedisClient.get()
