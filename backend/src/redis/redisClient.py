import redis.asyncio as redis
from src.config import settings


class RedisClient:
    """
    Singleton manager for the async Redis connection.

    Lazily creates one shared redis.asyncio.Redis client on first access and
    stores it as a class variable so the same connection pool is reused across
    all requests. Call close() during application shutdown to release the pool.
    """
    _client:redis.Redis | None = None

    @classmethod
    def get(cls) -> redis.Redis:
        """
        Returns the shared async Redis client, creating it on first call.

        Connection options:
          - encoding='utf-8'        : Decode all Redis responses as UTF-8 strings.
          - decode_responses=True   : Return str instead of bytes.
          - socket_timeout=2        : Fail fast if Redis is unreachable.
          - socket_keepalive=True   : Keep TCP connections alive.
          - health_check_interval=30: Periodically ping Redis to detect stale connections.

        Parameters:
          None

        Returns:
          redis.Redis: The singleton async Redis client instance.
        """
        if cls._client is None:
            cls._client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=2,
                socket_keepalive=True,
                health_check_interval=30,
            )
        return cls._client

    @classmethod
    async def close(cls) -> None:
        """
        Closes the Redis connection pool and resets the singleton.

        Should be called during application shutdown (e.g. in the lifespan handler)
        to cleanly release all TCP connections.

        Parameters:
          None

        Returns:
          None
        """
        if cls._client is not None:
            await cls._client.close()
            cls._client = None
def get_redis() -> redis.Redis:
    """
    FastAPI dependency that returns the shared async Redis client.

    Parameters:
      None

    Returns:
      redis.Redis: The singleton async Redis client from RedisClient.get().
    """
    return RedisClient.get()
