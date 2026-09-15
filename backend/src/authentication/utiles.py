from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from src.config import settings


def _create_token(
    data: str | Any,
    secret_key: str,
    expire_minutes: int,
    token_type: str,
) -> str:

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expire_minutes
    )

    payload = {
        "sub": str(data),
        "exp": expire,
        "type": token_type,
    }

    return jwt.encode(
        payload,
        secret_key,
        algorithm=settings.ENCRYPTION_ALGORITHM,
    )


def create_access_token(
    data: str | Any,
    expire_delta: timedelta | None = None,
) -> str:

    if expire_delta is not None:
        expire_minutes = int(
            expire_delta.total_seconds() / 60
        )
    else:
        expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    return _create_token(
        data=data,
        secret_key=settings.JWT_ACCESS_SECRET_KEY,
        expire_minutes=expire_minutes,
        token_type="access",
    )


def create_refresh_token(
    data: str | Any,
    expire_delta: timedelta | None = None,
) -> str:

    if expire_delta is not None:
        expire_minutes = int(
            expire_delta.total_seconds() / 60
        )
    else:
        expire_minutes = settings.REFRESH_TOKEN_EXPIRE_MINUTES

    return _create_token(
        data=data,
        secret_key=settings.JWT_REFRESH_SECRET_KEY,
        expire_minutes=expire_minutes,
        token_type="refresh",
    )


def verify_access_token(token: str) -> dict | None:

    try:
        payload = jwt.decode(
            token,
            settings.JWT_ACCESS_SECRET_KEY,
            algorithms=[
                settings.ENCRYPTION_ALGORITHM
            ],
        )

        if payload.get("type") != "access":
            return None

        if not payload.get("sub"):
            return None

        return payload

    except JWTError:
        return None


def verify_refresh_token(token: str) -> dict | None:

    try:
        payload = jwt.decode(
            token,
            settings.JWT_REFRESH_SECRET_KEY,
            algorithms=[
                settings.ENCRYPTION_ALGORITHM
            ],
        )

        if payload.get("type") != "refresh":
            return None

        if not payload.get("sub"):
            return None

        return payload

    except JWTError:
        return None



def verify_token(token: str) -> dict | None:
    return verify_access_token(token)