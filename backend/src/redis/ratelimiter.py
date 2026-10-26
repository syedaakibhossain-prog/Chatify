import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass

import redis.asyncio as redis
from fastapi import Depends, HTTPException, Request, status
from src.config import settings
from src.redis.redisClient import get_redis

logger = logging.getLogger("chatify")


@dataclass(frozen=True)
class RateLimite:
    """
    Immutable configuration for a rate limit rule.

    Attributes:
      limit (int)         : Maximum number of requests allowed within the window.
      window_second (int) : Duration of the sliding window in seconds.
    """
    limit: int
    window_second: int

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the rate limit rule.

        Returns:
          str: e.g. '5req/60s'
        """
        return f"{self.limit}req/{self.window_second}s"


# Sliding-window rate limit Lua script (atomic, runs server-side).
# Returns {1, 0} when allowed, {0, retry_after_ms} when blocked.
_SCRIPT = """
local key = KEYS[1]
local cutoff = tonumber(ARGV[1])
local now = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local window_ms = tonumber(ARGV[4])
local member = ARGV[5]

redis.call('ZREMRANGEBYSCORE', key, 0, cutoff)
local count = redis.call('ZCARD', key)

if count >= limit then
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry_after_ms = 0
    if oldest[2] then
        retry_after_ms = (tonumber(oldest[2]) + window_ms) - now
    end
    return {0, retry_after_ms}
end

redis.call('ZADD', key, now, member)
redis.call('PEXPIRE', key, window_ms)
return {1, 0}
"""


class RateLimiter:
    """
    Implements a Redis-backed sliding-window rate limiter.

    Uses a Lua script executed atomically on the Redis server to evaluate
    whether a request is within the allowed rate, preventing race conditions.
    """

    def __init__(self, redis_client: redis.Redis) -> None:
        """
        Initializes the RateLimiter with a Redis client.

        Parameters:
          redis_client (redis.Redis): The async Redis client to use for rate limit checks.
        """
        self.redis = redis_client

    async def check(
        self,
        scope: str,
        identity: str,
        rate: RateLimite,
    ) -> None:
        """
        Checks whether the given identity has exceeded the rate limit for the given scope.

        If rate limiting is disabled in settings, returns immediately. Otherwise,
        executes the sliding-window Lua script on Redis. If the limit is exceeded,
        raises HTTP 429 with a 'Retry-After' header.

        Parameters:
          scope (str)        : A string key grouping requests (e.g. 'auth:login').
          identity (str)     : A string identifying the requester (e.g. 'ip:1.2.3.4').
          rate (RateLimite)  : The rate limit rule (limit + window) to enforce.

        Returns:
          None

        Raises:
          HTTPException (429): If the rate limit is exceeded, with a Retry-After header.
        """

        if not settings.rate_limit_enabled:
            return

        key = f"rl:{scope}:{identity}"
        now_ms = int(time.time() * 1000)
        window_ms = rate.window_second * 1000
        cutoff_ms = now_ms - window_ms
        member = f"{now_ms}:{uuid.uuid4().hex}"

        allowed, retry_after_ms = await self.redis.eval(
            _SCRIPT,
            1,
            key,
            cutoff_ms,
            now_ms,
            rate.limit,
            window_ms,
            member,
        )

        if not allowed:
            retry_after = max(1, int(retry_after_ms / 1000))
            logger.warning(
                "rate_limit.blocked scope=%s identity=%s limit=%s retry_after=%ss",
                scope,
                identity,
                rate,
                retry_after,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {retry_after}s.",
                headers={"Retry-After": str(retry_after)},
            )


def client_ip(request: Request) -> str:
    """Extract real client IP, honouring X-Forwarded-For when trusted_proxy is set."""
    if settings.trusted_proxy:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(
    scope: str,
    rate: RateLimite,
    identity: Callable[[Request], str] | None = None,
):
    """
    FastAPI dependency factory for sliding-window rate limiting.

    Usage (as route dependency):
        @router.post("/login", dependencies=[Depends(rate_limit("auth:login", AUTH_LOGIN))])
        async def login(...): ...

    Or inline in the handler signature:
        async def login(..., _rl: None = Depends(rate_limit("auth:login", AUTH_LOGIN))): ...
    """
    identity_fn: Callable[[Request], str] = identity or (
        lambda r: f"ip:{client_ip(r)}"
    )

    async def _dependency(
        request: Request,
        redis_client: redis.Redis = Depends(get_redis),
    ) -> None:
        limiter = RateLimiter(redis_client=redis_client)
        await limiter.check(scope, identity_fn(request), rate)

    return _dependency
