from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    HTTPException,
    Response,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from src.authentication.reposetory import (
    UserRepository,
)
from src.authentication.schemas import (
    LoginRequest,
    UserRequest,
    UserResponse,
)
from src.authentication.service import (
    AuthService,
)
from src.database import get_db
from src.dependences import get_user

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)



def get_auth_service() -> AuthService:

    repository = UserRepository()

    return AuthService(
        repository
    )




def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
) -> None:

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )




@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_request: UserRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(
        get_auth_service
    ),
):

    user = await auth_service.register_user(
        user_request,
        db,
    )

    return user




@router.post(
    "/login",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def login(
    login_request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(
        get_auth_service
    ),
):

    user, access_token, refresh_token = (
        await auth_service.login_user(
            login_request,
            db,
        )
    )

    set_auth_cookies(
        response,
        access_token,
        refresh_token,
    )

    print("ACCESS TOKEN:", access_token)
    print("REFRESH TOKEN:", refresh_token)
    print("RESPONSE HEADERS:", response.headers)

    return UserResponse(
        user_id=user.id,
        username=user.username,
        email=user.email,
    )




@router.post(
    "/refresh",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(
        default=None
    ),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(
        get_auth_service
    ),
):

    if not refresh_token:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided",
        )

    user, access_token = (
        await auth_service.refresh_access_token(
            refresh_token,
            db,
        )
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60,
    )

    return UserResponse(
        user_id=user.id,
        username=user.username,
        email=user.email,
    )




@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout(
    response: Response,
):

    response.delete_cookie(
        key="access_token",
    )

    response.delete_cookie(
        key="refresh_token",
    )





@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def get_current_user(
    current_user=Depends(get_user),
):

    return UserResponse(
        user_id=current_user.id,
        username=current_user.username,
        email=current_user.email,
    )