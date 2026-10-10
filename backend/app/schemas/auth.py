"""Authentication schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.role import RoleBrief
from app.schemas.user import StudentProfileResponse


class LoginRequest(BaseModel):
    username: str = Field(
        ..., description="Username or e-mail address of the account.", examples=["admin@example.com"]
    )
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token lifetime in seconds.")


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=10, max_length=200)
    new_password: str = Field(..., min_length=8, max_length=128)


class MeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile: Optional[str] = None
    status: str
    is_verified: bool
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    roles: List[RoleBrief] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    student_profile: Optional[StudentProfileResponse] = None
