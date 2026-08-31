from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.model import User

from src.utils import (
    get_hashed_password,
    verify_password,
)

from src.authentication.reposetory import (
    UserRepository,
)

from src.authentication.schemas import (
    UserRequest,
    LoginRequest,
    UserResponse,
)

from src.authentication.utiles import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)


class AuthService:

    def __init__(
        self,
        user_repo: UserRepository,
    ):
        self.user_repo = user_repo



    async def register_user(
        self,
        user_request: UserRequest,
        db: AsyncSession,
    ) -> UserResponse:

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

        return UserResponse(
            user_id=created_user.id,
            username=created_user.username,
            email=created_user.email,
        )

    async def login_user(
        self,
        login_request: LoginRequest,
        db: AsyncSession,
    ) -> tuple[User, str, str]:

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

        user = await self.user_repo.get_user_by_id(
            db,
            user_id,
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