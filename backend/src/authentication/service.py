import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.authentication.reposetory import (
    UserRepository,
)
from src.authentication.schemas import (
    LoginRequest,
    UserRequest,
    UserResponse,
)
from src.authentication.utiles import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from src.model import User
from src.utils import (
    get_hashed_password,
    verify_password,
)


class AuthService:
    """
    Service layer handling all authentication business logic.

    Depends on UserRepository for database access. Provides methods to
    register new users, log existing users in, and refresh access tokens.
    """

    def __init__(
        self,
        user_repo: UserRepository,
    ):
        """
        Initializes the AuthService with a user repository.

        Parameters:
          user_repo (UserRepository): The repository used for all user-related DB operations.
        """
        self.user_repo = user_repo



    async def register_user(
        self,
        user_request: UserRequest,
        db: AsyncSession,
    ) -> tuple[UserResponse , str , str]:
        """
        Registers a new user account.

        Steps:
          1. Checks that the username is not already taken (raises 409 if it is).
          2. Checks that the email is not already registered (raises 409 if it is).
          3. Hashes the plain-text password with bcrypt.
          4. Creates and persists the User record in the database.
          5. Generates a JWT access token and refresh token for the new user.

        Parameters:
          user_request (UserRequest): Pydantic schema with username, email, and password.
          db (AsyncSession)         : The async database session.

        Returns:
          tuple[UserResponse, str, str]: A tuple of (UserResponse, access_token, refresh_token).

        Raises:
          HTTPException (409): If the username or email is already in use.
        """

        existing_username = (
            await self.user_repo.get_user_by_name(
                db,
                user_request.username,
            )
        )

        if existing_username:

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists",
            )

        existing_email = (
            await self.user_repo.get_user_by_email(
                db,
                user_request.email,
            )
        )

        if existing_email:

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists",
            )

        hashed_password = get_hashed_password(
            user_request.password
        )

        user = User(
            username=user_request.username,
            email=user_request.email,
            hashed_password=hashed_password,
        )

        created_user = (
            await self.user_repo.create_user(
                db,
                user,
            )
        )
        access_token = create_access_token(
            created_user.id
        )
        refresh_token = create_refresh_token(
            created_user.id
        )

        return (
            UserResponse(
                user_id=created_user.id,
                username=created_user.username,
                email=created_user.email,
            ),
            access_token,
            refresh_token
        )

    async def login_user(
        self,
        login_request: LoginRequest,
        db: AsyncSession,
    ) -> tuple[User, str, str]:
        """
        Authenticates a user and returns a session token pair.

        Steps:
          1. Looks up the user by email address (raises 401 if not found).
          2. Verifies the provided plain-text password against the stored bcrypt hash
             (raises 401 if the password does not match).
          3. Generates a new access token and refresh token.

        Parameters:
          login_request (LoginRequest): Pydantic schema with email and password.
          db (AsyncSession)           : The async database session.

        Returns:
          tuple[User, str, str]: A tuple of (User ORM object, access_token, refresh_token).

        Raises:
          HTTPException (401): If the email is not registered or the password is wrong.
        """

        # Find user

        user = (
            await self.user_repo.get_user_by_email(
                db,
                login_request.email,
            )
        )

        if not user:

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        # Verify password

        password_is_valid = verify_password(
            login_request.password,
            user.hashed_password,
        )

        if not password_is_valid:

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        # Create JWTs

        access_token = create_access_token(
            user.id
        )

        refresh_token = create_refresh_token(
            user.id
        )

        return (
            user,
            access_token,
            refresh_token,
        )

    async def refresh_access_token(
        self,
        refresh_token: str,
        db: AsyncSession,
    ) -> tuple[User, str]:
        """
        Issues a new access token using a valid refresh token.

        Steps:
          1. Verifies the refresh token's signature and expiry (raises 401 if invalid).
          2. Extracts the 'sub' (user ID) from the token payload.
          3. Parses the user ID string into a UUID (raises 401 if malformed).
          4. Fetches the User from the database (raises 401 if the account no longer exists).
          5. Creates and returns a fresh access token.

        Parameters:
          refresh_token (str) : The raw JWT refresh token string.
          db (AsyncSession)   : The async database session.

        Returns:
          tuple[User, str]: A tuple of (User ORM object, new_access_token).

        Raises:
          HTTPException (401): If the refresh token is invalid, expired, or the user is gone.
        """

        payload = verify_refresh_token(
            refresh_token
        )

        if not payload:

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        user_id = payload.get("sub")

        if not user_id:

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        try:
            user_uuid = uuid.UUID(user_id)
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload",
            )

        user = await self.user_repo.get_user_by_id(
            db,
            user_uuid,
        )

        if not user:

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User no longer exists",
            )

        access_token = create_access_token(
            user.id
        )

        return user, access_token
