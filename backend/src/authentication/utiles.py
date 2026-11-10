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
    """
    Internal helper that builds and signs a JWT token.

    Parameters:
      data (str | Any)     : The subject (typically a user UUID) to embed in the 'sub' claim.
      secret_key (str)     : The HMAC secret used to sign the token.
      expire_minutes (int) : How many minutes from now the token expires.
      token_type (str)     : A label stored in the 'type' claim ('access' or 'refresh'),
                             used during verification to prevent token type confusion.

    Returns:
      str: The signed, encoded JWT string.
    """

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
    """
    Creates a short-lived JWT access token for the given subject.

    Parameters:
      data (str | Any)               : The subject to encode (usually a user UUID).
      expire_delta (timedelta | None) : Custom expiry duration. If None, defaults to
                                        ACCESS_TOKEN_EXPIRE_MINUTES from settings.

    Returns:
      str: The signed JWT access token string.
    """

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
    """
    Creates a long-lived JWT refresh token for the given subject.

    Parameters:
      data (str | Any)               : The subject to encode (usually a user UUID).
      expire_delta (timedelta | None) : Custom expiry duration. If None, defaults to
                                        REFRESH_TOKEN_EXPIRE_MINUTES from settings.

    Returns:
      str: The signed JWT refresh token string.
    """

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
    """
    Decodes and validates a JWT access token.

    Rejects the token if it is expired, has an invalid signature, is of the
    wrong type ('refresh' instead of 'access'), or is missing the 'sub' claim.

    Parameters:
      token (str): The raw JWT string to verify.

    Returns:
      dict | None: The decoded payload dict if valid, or None if the token is invalid.
    """

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
    """
    Decodes and validates a JWT refresh token.

    Rejects the token if it is expired, has an invalid signature, is of the
    wrong type ('access' instead of 'refresh'), or is missing the 'sub' claim.

    Parameters:
      token (str): The raw JWT string to verify.

    Returns:
      dict | None: The decoded payload dict if valid, or None if the token is invalid.
    """

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
    """
    Public alias for verify_access_token.

    Parameters:
      token (str): The raw JWT access token string.

    Returns:
      dict | None: The decoded payload dict if valid, or None if invalid.
    """
    return verify_access_token(token)