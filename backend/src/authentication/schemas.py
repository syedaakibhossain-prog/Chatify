from pydantic import (
    UUID4,
    BaseModel,
    EmailStr,
    Field,
)


class UserRequest(BaseModel):

    username: str = Field(
        min_length=3,
        max_length=20,
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=70,
    )


class LoginRequest(BaseModel):

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserResponse(BaseModel):

    user_id: UUID4
    username: str
    email: EmailStr