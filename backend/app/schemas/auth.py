from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class StoreCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    address: str | None = None


class StoreResponse(BaseModel):
    id: str
    name: str
    address: str | None
    role: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class EmailRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=12, max_length=128)


class UserResponse(BaseModel):
    id: str
    email: EmailStr
